---
title: Cable State Estimation Phase 3 Integration Design (Stages A-E end-to-end + Q5 benchmark protocol)
created: '2026-05-04T05:05:00+09:00'
tags:
  - knowledge
  - vision
  - cable-state
  - phase-3-integration-design
  - design-reference
status: design (T-Vision-CableState-Impl-Phase-3-Integration-Design-CC、Phase 3 = end-to-end integration design + Q5 benchmark protocol scope only、impl + train + benchmark execution は Phase 4-6 別 NEST node)
node_id: T-Vision-CableState-Impl-Phase-3-Integration-Design
session: T-Vision-CableState-Impl-Phase-3-Integration-Design-CC
parent_memo: thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md
sibling_memo: thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase2-Impl-Design.md
doc_class: design-surface
---

# LL-Vision-CableState-Phase3-Integration-Design

> T-Vision-CableState 5-stage pipeline (Hybrid PCA + Cosserat) **Phase 3 end-to-end integration design** memo。Phase 1 (Stage A.3 + B、`MultiCamCableStatePipeline` COMPLETE 2026-05-04T03:50) と Phase 2 (Stage C/D/E component skeleton COMPLETE 2026-05-04T03:55) を `cable_state.py` の `CableStateSolver` 経で orchestrate する pipeline-level data-flow + module boundary + Q5 worst-case benchmark protocol を locking。
>
> **scope:** design only。impl + train + benchmark execution は Phase 4 (Stage C train、~25h GPU) / Phase 5 (Stage D/E impl) / Phase 6 (Q5 benchmark execution) で起票。
>
> **base:** parent memo §2 全 (5-stage pipeline architecture)、§3 (topology preservation)、§5 (benchmark spec)、§6 (R6 boundary integration); Phase 2 memo §2 (Stage C concrete spec)、§3 (Stage D)、§4 (Stage E)、§5 (Phase 1 → Phase 2 integration component-level)。
>
> **boundary:** R6 input-boundary 遵守。本 leaf は doc-only、`cable_state.py` / `vision_pipeline.py` / `wrist_camera_manager.py` / `cable_state_*.py` skeletons / `task_config.py` / `04-Specs/*.md` / `types.py` 全 TOUCH FORBIDDEN。

---

## §0 Executive summary

- **Phase 3 = end-to-end integration design + Q5 benchmark protocol design** scope。本 memo の deliverable は doc-only、code 改変なし。Phase 4-6 起票時の spec source として機能。
- **Pipeline architecture full**: Phase 1 `MultiCamCableStatePipeline.estimate(finger_positions, prev)` → `CableStatePhase1Result` (40×3 NaN-fillable + var_ratio + bin_counts + n_pts + fallback_reason + succeeded) → `CableStateSolver.__call__(cloud, phase1_result, prev, finger)` → conditional Stage C trigger (var_ratio < 0.6) → Stage D Cosserat fit → identity inversion check → Stage E confidence calibration → `CableState40` (positions [40,3] + confidences [40] + stage_diagnostics dict)
- **Module boundary**: file ownership matrix 7 file × 6 stage、Phase 1 freeze + Phase 2 freeze + Phase 5 impl scope を明確分離 (§3.1)
- **Q5 benchmark protocol**: eval dataset generator (N=100 random + 10 U + 10 S worst-case) + per-scene evaluation function + PASS criteria evaluator + per-stage diagnostics aggregator の 4 要素を implementation-ready level で spec、Phase 6 boilerplate elimination
- **Per-stage latency budget**: Stage A 5ms / Stage B 5ms / Stage C 2ms / Stage D 30ms / Stage E 5ms / Identity check 3ms = **50ms total** (parent §2.5.3 + §5.4 reference)、warm start 経で typical 30-40ms 想定
- **Phase 番号 renumber**: 原 Phase 2 memo §9.4 では "Phase 3 = Stage C train"。本 task が "Phase 3 = Integration Design" を占有、原 Phase 3-5 は Phase 4-6 に shift (本 §1.4)

---

## §1 Scope & Phase renumber

### §1.1 In-scope (本 Phase 3 design phase)

1. **End-to-end data flow spec** (§2): Phase 1 → Phase 2 components 接続の adapter logic、NaN handling、var_ratio gate dispatcher、stage transition contract
2. **Module boundary matrix** (§3, §4): file ownership × stage、R6 enforcement、Phase 1/2/5 impl scope 明確分離
3. **`CableStateSolver` orchestration pattern** (§3): Phase 5 impl reference (constructor + `__call__` + `_stage_*` delegate + `stage_diagnostics` aggregation)
4. **Q5 worst-case benchmark protocol** (§5): eval dataset generator function signature、per-scene metric function、PASS criteria evaluator、diagnostics aggregator
5. **Latency budget** (§6): per-stage allocation + total budget 50ms feasibility
6. **Failure mode tabulation** (§7): F1-F12 mode + mitigation chain (parent §5.5 拡張)
7. **Phase 4-6 trigger spec** (§8): cascade dependency + spec source pin

### §1.2 Out-of-scope (Phase 4-6 別 NEST node)

- Phase 4 (`T-Vision-CableState-Impl-Phase-4-Stage-C-Train`): Stage C DD-PINN train (~25h GPU + 5k labeled scenes generation infrastructure + checkpoint 生成)
- Phase 5 (`T-Vision-CableState-Impl-Phase-5-Stage-DE`): Stage D Cosserat 7-term loss impl (PyTorch L-BFGS gradient computation + multi-restart + identity inversion check) + Stage E ECE calibration (val 1k sample logistic regression coefficient fit) + `cable_state.py` `CableStateSolver` orchestrator delegate fill
- Phase 6 (`T-Vision-CableState-Impl-Phase-6-Q5-Bench`): Q5 worst-case benchmark execution (10 U + 10 S scripted scenes + N=100 random + ECE measurement + identity inversion 0% verify + latency p95 <50ms verify)
- Warp kernel optimization (latency-critical 化判断は Phase 6 latency profile 経で defer、別 leaf `T-Vision-CableState-Impl-Phase-7-Warp` 候補)
- 04-Specs SSOT update (Rs専権、Vault Write Permissions)
- env file / `cable_state*.py` impl-time 改変 (本 Phase 3 では reference のみ)

### §1.3 Phase 3 deliverable summary

| deliverable | path | LoC est. | status |
|-------------|------|----------|--------|
| state.md | `T-Vision-CableState-Impl-Phase-3-Integration-Design/state.md` | ~150 | (本 leaf) |
| design memo | `06-Knowledge/LL-Vision-CableState-Phase3-Integration-Design.md` (本 file) | ~600 | (本 leaf) |
| parent state update | `T-Vision-CableState/state.md` | +5 | (本 leaf) |
| manifest update | `00-Project-Management/project-tree-manifest.md` | +15 | (本 leaf) |
| Tier 2 deposit | `_edit_requests/00014-T-Vision-CableState-Impl-Phase-3-Integration-Design-init.md` | ~150 | (本 leaf) |
| memory entry | `~/.claude/projects/.../memory/project_t_vision_cable_state_impl_phase3_integration_design_2026-05-04.md` | ~50 | (本 leaf) |

### §1.4 Phase 番号 renumber (Phase 2 design memo との整合)

原 Phase 2 design memo (`LL-Vision-CableState-Phase2-Impl-Design.md` §1.2 + §9.4 line 769-786) では:

| 旧 Phase | 内容 | LoC + GPU |
|----------|------|-----------|
| Phase 3 | Stage C DD-PINN train | ~180 LoC + ~25h GPU |
| Phase 4 | Stage D Cosserat impl + Stage E ECE calibration | ~200 LoC + ~7h GPU |
| Phase 5 | Q5 worst-case benchmark execution | ~80 LoC + ~5h GPU |

Rs directive (`T-Vision-CableState-Impl-Phase-3-Integration-Design`) 経で本 task が "Phase 3 = Integration Design" を占有、よって以降の renumber:

| 新 Phase | 内容 | LoC + GPU | 起票 trigger |
|----------|------|-----------|--------------|
| Phase 1 (unchanged) | Stage A.3 + B + camera infra (COMPLETE 2026-05-04T03:50) | ~580 LoC + 0 GPU | (済) |
| Phase 2 (unchanged) | Stage C/D/E design + skeleton (COMPLETE 2026-05-04T03:55) | ~580 LoC + 0 GPU | (済) |
| **Phase 3 (NEW、本 leaf)** | **Stages A-E integration design + Q5 benchmark protocol** | **~600 行 doc + 0 GPU + ~1-2h wall** | (本 leaf 進行中) |
| Phase 4 (旧 Phase 3) | Stage C train | ~180 LoC + ~25h GPU | 5k dataset ready + Rs §3.1 #4 |
| Phase 5 (旧 Phase 4) | Stage D Cosserat impl + Stage E ECE calibration | ~200 LoC + ~7h GPU | Phase 4 PASS + 1k val held-out |
| Phase 6 (旧 Phase 5) | Q5 worst-case benchmark execution | ~80 LoC + ~5h GPU | Phase 5 COMPLETE + 10U/10S scripted scene env-side ready |

**注 (Phase 5 = Stage D/E impl への影響):** Phase 5 起票時、本 design memo §3 の orchestration pattern を `cable_state.py` `CableStateSolver` の delegate fill in に impl 経。即ち本 leaf design は Phase 5 の spec source。

---

## §2 Stages A-E end-to-end data flow

### §2.1 Pipeline overview diagram (full、Phase 1 + 2 統合 view)

```
Inputs (env + camera):
  rgb_l, rgb_r, rgb_oh                   ∈ [B, 3, H, W]
  depth_l, depth_r, depth_oh             ∈ [B, 1, H, W]
  wrist_camera_pose_l, wrist_camera_pose_r, overhead_camera_pose ∈ [B, 7]
  wrist_intrinsics_l, wrist_intrinsics_r, overhead_intrinsics    ∈ [B, 3, 3]
  finger_positions (optional)            ∈ [2, 3]   (left + right finger world xyz)
  previous_cable_estimate (optional)      = CableState40 from prev frame

──────────────────────────────────────────────────────────────────────────
Stage A.1 (existing/Phase 1 substrate): per-cam Cable mask
  - HSV mask (Phase 1) OR 9-class semantic seg (MVP-0B v2 ready 後)
  - input: rgb_c (per cam c ∈ {wrist_L, wrist_R, overhead})
  - output: mask_c ∈ {0, 255} binary

Stage A.2 (Phase 1 substrate): per-cam depth back-projection
  - input: mask_c + depth_c + intrinsics_c + camera_pose_c
  - inverse pinhole projection + camera→world transform
  - output: P_c ∈ ℝ^(N_c × 3) per cam world-frame points

Stage A.3 (Phase 1 NEW): multi-cam fusion + voxel downsample
  - location: thread_isaac_lab/models/vision_pipeline.py
              MultiCamCableStatePipeline.estimate() internally calls
              voxel_downsample_points() with per_cam_points list
  - input: [P_wrist_L, P_wrist_R, P_overhead]
  - voxel hash dedupe at ε=2mm (np.unique O(N log N))
  - output: P_merged ∈ ℝ^(N_pts × 3), expected N_pts ~1500-3000

  ↓ N_pts < 800 → FAIL_CLOSED (succeeded=False, fallback_reason="n_pts<800")
  ↓ N_pts ≥ 800 → continue

Stage B (Phase 1 NEW): PCA principal axis + 40-bin arc-length discretize
  - location: vision_pipeline.MultiCamCableStatePipeline.estimate()
              → discretize_arc_length_40bins() helper
  - input: P_merged + finger_positions (handedness anchor) + prev (Tier 2 not connected in Phase 1)
  - SVD: principal direction d ∈ ℝ³, var_ratio ∈ [0, 1]
  - 40-bin centroid + handedness anchor (Tier 1 finger / Tier 3 t_min default)
  - output: CableStatePhase1Result {
      seg_positions: [40, 3] NaN-fillable,
      bin_counts:    [40] int (per-bin point count),
      var_ratio:     float,
      n_pts:         int (after voxel),
      fallback_reason: Optional[str],
      succeeded:     bool,
    }

──────────────────────────────────────────────────────────────────────────
[Phase 1 → Phase 2 boundary、本 leaf §2.2-§2.4 で adapter spec]
──────────────────────────────────────────────────────────────────────────

Phase 2 entry: CableStateSolver.__call__(
  cloud,                    ← P_merged (Phase 1 internal output, expose via Phase 1 API extension OR re-derive)
  phase1_result,            ← CableStatePhase1Result
  prev,                     ← previous_cable_estimate
  finger_positions,
)

  ↓ if not phase1_result.succeeded:
       return CableState40(
         positions=prev.positions if prev else zeros[40, 3],
         confidences=zeros[40],
         stage_diagnostics={"fallback": phase1_result.fallback_reason, ...}
       )

  ↓ phase1_result.succeeded == True:

Stage B output → Stage C/D dispatcher (var_ratio gate):
  ┌─ var_ratio ≥ 0.6 (random scene、PCA single-axis sufficient):
  │      seg_init = nan_fill_zero(phase1_result.seg_positions)
  │      bypass Stage C
  │
  └─ var_ratio < 0.6 (U/S worst-case、PCA fail):
         seg_init_pre_C = nan_fill_zero(phase1_result.seg_positions)
         seg_init = self._dd_pinn(cloud, prev)        ← Stage C DDPINNModel.forward
         (Stage C output: [40, 3] warm-start, no NaN)

Stage D (Phase 2 freeze、Phase 5 impl):
  seg_fitted = self._cosserat.fit(
    seg_init=seg_init,                        # [40, 3] from Stage B or C
    cloud=cloud,                              # [N_pts, 3] from Stage A.3
    prev=prev,                                # CableState40 | None
    finger_positions=finger_positions,        # [2, 3] | None
  )
  # internal: 7-term Cosserat loss + L-BFGS + 5-restart σ=2mm + max_iter=200

Identity inversion check (Phase 2 spec § 3.5 + parent §3.3):
  seg_verified = self._cosserat._verify_identity(seg_fitted, finger_positions)
  # if d_grasp > d_far + 50mm → reverse + 1-pass refit

Stage E (Phase 2 freeze、Phase 5 impl):
  signals = self._confidence.compute_signals(
    seg=seg_verified,
    cloud=cloud,
    prev=prev,
    camera_poses=[pose_l, pose_r, pose_oh],
    camera_intrinsics=[K_l, K_r, K_oh],
  )
  # 5 signals: visibility, density, residual, curvature, temporal

  c = self._confidence.aggregate(signals, alpha, beta)
  # alpha, beta: post-train logistic regression coefficients (Phase 5 calibrated)

──────────────────────────────────────────────────────────────────────────

Output: CableState40 {
  positions:         seg_verified ∈ ℝ^(40, 3) world-frame,
  confidences:       c ∈ [0, 1]^40,
  stage_diagnostics: {
    "stage_a3": {"n_pts": int, "n_pts_per_cam": [int, int, int]},
    "stage_b":  {"var_ratio": float, "bin_counts": [int]^40, "L_est": float},
    "stage_c_triggered": bool,
    "stage_c": {"latency_ms": float} if triggered else None,
    "stage_d": {"final_loss": float, "iter_count": int, "restart_used": int, "latency_ms": float},
    "identity_inversion_detected": bool,
    "stage_e": {"ece_estimate": float | None, "latency_ms": float},
    "total_latency_ms": float,
  },
}
```

### §2.2 Phase 1 → Phase 2 cloud propagation

**Issue**: Phase 1 `MultiCamCableStatePipeline.estimate()` internally produces `P_merged` (Stage A.3 output) but `CableStatePhase1Result` does NOT expose it (Phase 1 API freeze、本 leaf TOUCH FORBIDDEN)。Phase 2 Stage C/D は cloud P_merged を input として要する (Stage C anchor sampling、Stage D L_pos NN search)。

**Adapter resolution options**:

| option | mechanism | Phase 1 impact | Phase 5 impl complexity |
|--------|-----------|----------------|-------------------------|
| (a) re-derive cloud from inputs | Phase 5 で `CableStateSolver` 内 `stage_a3_fuse_clouds()` 再呼び出し | Phase 1 freeze 維持 | duplicate Stage A.3 work (~5ms latency overhead) |
| (b) pass cloud through external API | `CableStateSolver.__call__(cloud=..., phase1_result=...)` で caller (env-side wrapper) が cloud + phase1_result 両方 inject | Phase 1 freeze 維持、env-side wrapper で Phase 1 API extension responsibility | env-side wrapper にやや複雑性追加、但し Phase 1 internal が exposable な adapter helper を Phase 5 で追加 (`MultiCamCableStatePipeline.estimate_with_cloud()` 等、新規 method) |
| (c) Phase 1 API 拡張 | Phase 1 freeze 緩和、`CableStatePhase1Result.cloud: torch.Tensor` field 追加 | Phase 1 freeze 違反 | clean、但し Phase 1 backward compat 影響 (caller SOMA Stage 1-3) |

**Phase 3 design 採択: option (b)** — env-side wrapper が cloud + phase1_result 両方 inject、Phase 5 で adapter helper method を Phase 1 API 拡張なしで `vision_pipeline.py` に追加 (新規 method、既存 API 不変、backward compat 維持)。

**Phase 5 impl pattern (reference)**:

```python
# vision_pipeline.py に Phase 5 で追加 (本 Phase 3 では design only):
class MultiCamCableStatePipeline:
    def estimate_with_cloud(
        self,
        finger_positions: torch.Tensor | None = None,
        prev: CableState40 | None = None,
    ) -> tuple[CableStatePhase1Result, torch.Tensor]:
        """Phase 1 estimate() + cloud expose。Phase 5 で Phase 2 components 接続用。

        Returns:
            (phase1_result, cloud) — cloud は Stage A.3 voxel-fused merged points [N_pts, 3]。
        """
        # internal: estimate() の logic を re-arrange、cloud を最終 return に追加
        # 既存 estimate() は backward compat 維持 (caller SOMA Stage 1-3 は cloud 不要)
        ...
```

env-side wrapper (例えば `EstimatorInputAdapter` の Phase 5 拡張、本 Phase 3 では design only):

```python
# Phase 5 reference pattern:
def _run_cable_state_phase2(env_inputs, pipeline, solver, prev, finger):
    phase1_result, cloud = pipeline.estimate_with_cloud(finger, prev)
    cable_state = solver(
        cloud=cloud,
        phase1_result=phase1_result,
        prev=prev,
        finger_positions=finger,
    )
    return cable_state
```

### §2.3 NaN handling end-to-end (parent §2.3.3 + Phase 2 §5.2 拡張)

`CableStatePhase1Result.seg_positions` は empty bin で NaN を含み得る (Phase 1 spec § 2.3.3)。Phase 2 components の取り扱い:

| stage | NaN segment treatment | gradient stability |
|-------|----------------------|--------------------|
| Stage C DD-PINN input | `seg_init = torch.nan_to_num(phase1_result.seg_positions, nan=0.0)`、prev_estimate も同様 zero-fill。Stage C は anchor-based reconstruction なので zero anchor を robust に処理 (architecture spec) | training-time loss は GT supervision、inference NaN-fill は安全 |
| Stage D L_pos | NN search 時に NaN segment は `torch.cdist(seg, cloud)` で NaN propagation → masked sum で contribution skip。`mask_valid = ~isnan(seg).any(dim=1) ∈ Bool^40`、L_pos = (mask_valid.float() * per_seg_residual).sum() / max(1, mask_valid.sum()) | mask_valid 経で NaN gradient 遮断、PyTorch autograd 安全 |
| Stage D L_arc | 連続 NaN segments の場合 (i NaN AND i+1 NaN) は arc-length 計算 NaN → contribution skip、(i NaN AND i+1 valid) は周辺 valid との distance penalty 適用。実装: pairwise mask + masked sum | mask 経で NaN gradient 遮断 |
| Stage D L_temp | NaN segment は prev[i] との difference が NaN → mask 経 skip。但し prev[i] も NaN の場合 (連続 NaN frames) は contribution 0 | 同上 |
| Stage D L_id | finger_positions 経の anchor は NaN 関与なし、L_id 計算は seg[0] と seg[39] の値依存。両端 NaN の場合 contribution 0 | mask 経で NaN gradient 遮断 |
| Stage E | NaN segment は s_visibility=0、s_density=0、s_residual=0、s_curvature=0、s_temporal=0 → c_i ≈ sigmoid(β) ≈ low confidence | 全 zero-fill で safe |
| Output | `CableState40.positions` は NaN を維持 (caller / downstream に意思を transparent transmit)、`confidences` は zero (低 confidence) | downstream T-Vision-Fusion では NaN segment を vision_state[i] = 0 + low conf で fold-in (parent §6.4 Late Fusion) |

**境界 case (連続 NaN segments 多数)**:

| 連続 NaN count | action |
|----------------|--------|
| ≤ 4 segments 連続 | Stage D L_arc + L_temp で interp の効果あり、Stage E で low conf 報告 |
| 5+ segments 連続 | parent §2.3.3 row 3 で "Stage D infill via temporal interp" 想定だが、本 Phase 3 design では Stage D 単独で interp 不可と判断 (L_arc + L_temp 局所 constraint のみ)。Phase 6 worst-case 観察で empirical confirm、必要なら Stage C trigger forced を考慮 (現 design では var_ratio < 0.6 のみが Stage C trigger) |

**Phase 6 monitoring item**: 連続 NaN count distribution per scene、5+ 観察時 Stage C trigger condition 拡張候補 (`var_ratio < 0.6 OR consecutive_nan ≥ 5`)。本 Phase 3 では現 condition 維持、Phase 6 で empirical revise。

### §2.4 var_ratio gate dispatcher (Stage C trigger)

```python
# Phase 5 impl reference pattern (CableStateSolver.__call__ 内):
def __call__(self, cloud, phase1_result, prev=None, finger_positions=None) -> CableState40:
    # Stage A failure short-circuit
    if not phase1_result.succeeded:
        return self._fallback(prev, phase1_result.fallback_reason)
    
    # Stage B output: NaN-fill for downstream stages
    seg_b = torch.nan_to_num(phase1_result.seg_positions, nan=0.0)
    
    # Stage C/D dispatcher (var_ratio gate)
    if phase1_result.var_ratio < self._config.var_ratio_threshold:
        # U/S worst-case: invoke DD-PINN warm start
        seg_init = self._dd_pinn(cloud, prev)
        stage_c_triggered = True
    else:
        # random scene: bypass Stage C
        seg_init = seg_b
        stage_c_triggered = False
    
    # Stage D Cosserat fit
    seg_fitted = self._cosserat.fit(seg_init, cloud, prev, finger_positions)
    
    # Identity inversion check (Stage D 内 1-pass refit)
    seg_verified = self._cosserat._verify_identity(seg_fitted, finger_positions)
    
    # Stage E confidence
    signals = self._confidence.compute_signals(
        seg_verified, cloud, prev,
        camera_poses=[...], camera_intrinsics=[...],
    )
    confidences = self._confidence.aggregate(
        signals, self._stage_e_alpha, self._stage_e_beta,
    )
    
    return CableState40(
        positions=seg_verified,
        confidences=confidences,
        stage_diagnostics={...},  # see § 3.4
    )
```

**threshold spec**: `var_ratio_threshold = 0.6` (parent §2.3.3 既存、`cable_state.py:84` `_DEFAULT_VAR_RATIO_THRESHOLD`)。Phase 6 worst-case observation 経で revision candidate (本 leaf §8 OQ-P3-2 + Phase 2 §5.2 OQ-P2-6 既存 issue)。

### §2.5 Stage transition contract

| transition | input contract | output contract | failure mode | mitigation |
|------------|----------------|-----------------|--------------|------------|
| A→B | merged cloud [N_pts, 3], N_pts ≥ 800 | seg_positions [40, 3] NaN-fillable + var_ratio + bin_counts | N_pts < 800 → FAIL_CLOSED at Phase 1 | prev_estimate fallback (or zeros if no prev) |
| B→C/D dispatcher | var_ratio ∈ [0, 1] + seg_positions | bool stage_c_triggered + seg_init [40, 3] no NaN | var_ratio NaN (degenerate cloud) → defensive: trigger Stage C | NaN-aware dispatcher: `stage_c_triggered = (var_ratio is None) or torch.isnan(var_ratio) or var_ratio < threshold` |
| B→D direct | seg_positions NaN-filled to zero | seg_init [40, 3] | identical to seg_b | (same as above) |
| C→D | seg_init [40, 3] no NaN | seg_init [40, 3] no NaN | DD-PINN inference fail (uninitialized model、checkpoint missing) → assertion at solver init | Phase 5 impl: `__init__` で checkpoint validity check + raise RuntimeError if checkpoint absent |
| D→identity check | seg_fitted [40, 3] | seg_verified [40, 3] | finger_positions absent → skip check (return seg_fitted unchanged) | Phase 2 §3.5 既存 spec |
| identity→E | seg_verified [40, 3] | confidences [40] | signals NaN propagation → safe via §2.3 mask | mask_valid handling per signal |

---

## §3 `CableStateSolver` orchestration pattern (Phase 5 impl reference)

### §3.1 File ownership matrix (本 leaf 中核 contribution)

| stage | owner file | function/method | impl status | Phase 5 impl scope |
|-------|------------|-----------------|-------------|---------------------|
| A.1 (mask) | `models/vision_pipeline.py` (Phase 1 freeze) | `VisionPipelineStage1to3._cable_mask` (existing HSV) + future `LightUNet9Class` (MVP-0B v2 ready 経) | Phase 1 DONE (HSV) | (Phase 5 では UNCHANGED) |
| A.2 (back-projection) | `models/vision_pipeline.py` (Phase 1 freeze) | `VisionPipelineStage1to3._backproject_mask` (existing) + per-cam variant in `MultiCamCableStatePipeline._backproject_per_cam` | Phase 1 DONE | (Phase 5 では UNCHANGED) |
| A.3 (fusion) | `models/vision_pipeline.py` + `estimators/cable_state.py` | `voxel_downsample_points` (Phase 1 in vision_pipeline.py) + `stage_a3_fuse_clouds` (Phase 2 skeleton in cable_state.py) | Phase 1 DONE (vision_pipeline.py side) + Phase 2 SKELETON (cable_state.py side、未 impl) | Phase 5: `cable_state.py` `stage_a3_fuse_clouds` impl OR delegate to `vision_pipeline.voxel_downsample_points` (recommended) |
| B (PCA + 40-bin) | `models/vision_pipeline.py` (Phase 1 freeze) | `discretize_arc_length_40bins` + `MultiCamCableStatePipeline.estimate` | Phase 1 DONE | (Phase 5 では UNCHANGED) |
| C (DD-PINN) | `estimators/cable_state_dd_pinn.py` (Phase 2 skeleton freeze) | `DDPINNModel.forward` + `farthest_point_sampling` | Phase 2 SKELETON (NotImplementedError) | Phase 5: `forward` impl + checkpoint loading (Phase 4 で train、Phase 5 で inference impl) |
| D (Cosserat) | `estimators/cable_state_cosserat.py` (Phase 2 skeleton freeze) | `CosseratSolver.fit` + `_compute_loss` + `_verify_identity` | Phase 2 SKELETON | Phase 5: 7-term loss closure + L-BFGS + multi-restart + identity inversion impl |
| E (confidence) | `estimators/cable_state_confidence.py` (Phase 2 skeleton freeze) | `ConfidenceCalibrator.compute_signals` + `aggregate` + `LogisticCalibrator.fit` + `compute_ece` | Phase 2 SKELETON | Phase 5: signals computation + sigmoid aggregation + post-train logistic regression impl |
| **orchestrator** | **`estimators/cable_state.py` (Phase 5 impl scope)** | **`CableStateSolver.__init__` + `__call__` + `_stage_*` delegate** | Phase 1 期 SKELETON (`stage_a3_fuse_clouds` + `CableStateSolver` class) | **Phase 5 impl**: constructor で 3 sub-modules inject + `_stage_b/c/d/e` メソッド body fill (delegate) + `__call__` で var_ratio dispatcher + diagnostics aggregation |

**注**: orchestrator (`cable_state.py`) は Phase 1 期に skeleton として 起票済 (382 LoC、`CableStateSolver` class with `_stage_b/c/d/e` raising NotImplementedError)。Phase 5 impl で 3 sub-modules を delegate するように body fill。本 Phase 3 では reference のみ、`cable_state.py` は UNCHANGED。

### §3.2 `CableStateSolver` constructor pattern (Phase 5 impl reference)

```python
# Phase 5 impl pattern (本 Phase 3 では reference only):
class CableStateSolver:
    """Hybrid PCA + Cosserat 5-stage cable state estimation orchestrator.

    Phase 5 impl で 3 Phase 2 sub-modules を delegate:
    - Stage C: cable_state_dd_pinn.DDPINNModel
    - Stage D: cable_state_cosserat.CosseratSolver
    - Stage E: cable_state_confidence.ConfidenceCalibrator
    """

    def __init__(
        self,
        dd_pinn: "DDPINNModel | None" = None,
        cosserat: "CosseratSolver | None" = None,
        confidence: "ConfidenceCalibrator | None" = None,
        config: CableStateSolverConfig | None = None,
        stage_e_alpha: torch.Tensor | None = None,        # [5] post-train logistic regression coef
        stage_e_beta: float | None = None,
    ) -> None:
        self._dd_pinn = dd_pinn
        self._cosserat = cosserat
        self._confidence = confidence
        self._config = config or CableStateSolverConfig()
        self._stage_e_alpha = stage_e_alpha   # Phase 5 で calibration 後 inject
        self._stage_e_beta = stage_e_beta

        # Phase 5 impl 時 invariants check:
        # - if dd_pinn is None and var_ratio_threshold < 1.0:
        #     raise RuntimeError("DD-PINN required for var_ratio gate")
        # - if cosserat is None: raise (Stage D 必須)
        # - if confidence is None: raise (Stage E 必須)
        # - if stage_e_alpha is None: warn (uncalibrated → uniform 0.5 fallback)
```

### §3.3 `__call__` method spec (Phase 5 impl reference)

```python
def __call__(
    self,
    cloud: torch.Tensor,                     # [N_pts, 3] from Stage A.3
    phase1_result: "CableStatePhase1Result", # Phase 1 output
    prev: CableState40 | None = None,
    finger_positions: torch.Tensor | None = None,  # [2, 3] left + right finger world xyz
) -> CableState40:
    """5-stage pipeline orchestration. Phase 5 impl scope.

    Args:
        cloud: voxel-fused merged points (Stage A.3 output、env-side wrapper expose).
        phase1_result: Stage A → B output dataclass.
        prev: previous frame estimate (None if episode start).
        finger_positions: gripper finger world positions (None if no grasp).

    Returns:
        CableState40 with positions, confidences, stage_diagnostics.

    Raises:
        RuntimeError: if Phase 5 impl 時 invariants check 失敗 (e.g., 必須 sub-module None).
    """
    t_start = time.perf_counter()

    # Stage A failure short-circuit
    if not phase1_result.succeeded:
        return self._fallback(prev, phase1_result.fallback_reason, t_start)

    # Stage B output → Stage C dispatcher
    seg_b = torch.nan_to_num(phase1_result.seg_positions, nan=0.0)
    use_stage_c = self._should_trigger_stage_c(phase1_result.var_ratio)

    if use_stage_c:
        t_c = time.perf_counter()
        seg_init = self._dd_pinn(cloud, prev)
        latency_c = (time.perf_counter() - t_c) * 1000.0
    else:
        seg_init = seg_b
        latency_c = None

    # Stage D Cosserat fit
    t_d = time.perf_counter()
    seg_fitted, d_diag = self._cosserat.fit(seg_init, cloud, prev, finger_positions)
    latency_d = (time.perf_counter() - t_d) * 1000.0

    # Identity inversion check (Stage D 内 1-pass refit)
    inv_detected = False
    if finger_positions is not None:
        seg_verified, inv_detected = self._cosserat._verify_identity(seg_fitted, finger_positions)
    else:
        seg_verified = seg_fitted

    # Stage E confidence
    t_e = time.perf_counter()
    signals = self._confidence.compute_signals(
        seg_verified, cloud, prev,
        # camera_poses + camera_intrinsics の env-side wrapper inject、本 Phase 3 では abstract
    )
    if self._stage_e_alpha is not None:
        confidences = self._confidence.aggregate(signals, self._stage_e_alpha, self._stage_e_beta)
    else:
        confidences = torch.full((40,), 0.5)  # uncalibrated fallback
    latency_e = (time.perf_counter() - t_e) * 1000.0

    total_latency = (time.perf_counter() - t_start) * 1000.0

    return CableState40(
        positions=seg_verified,
        confidences=confidences,
        stage_diagnostics={
            "stage_a3": {"n_pts": phase1_result.n_pts},
            "stage_b": {
                "var_ratio": phase1_result.var_ratio,
                "bin_counts": phase1_result.bin_counts.tolist(),
            },
            "stage_c_triggered": use_stage_c,
            "stage_c": {"latency_ms": latency_c} if use_stage_c else None,
            "stage_d": {**d_diag, "latency_ms": latency_d},
            "identity_inversion_detected": inv_detected,
            "stage_e": {"latency_ms": latency_e},
            "total_latency_ms": total_latency,
        },
    )

def _should_trigger_stage_c(self, var_ratio: float | None) -> bool:
    """var_ratio gate (defensive against NaN / None)."""
    if var_ratio is None or (isinstance(var_ratio, float) and math.isnan(var_ratio)):
        return True   # degenerate → trigger Stage C as safe rescue
    return var_ratio < self._config.var_ratio_threshold

def _fallback(self, prev, reason, t_start) -> CableState40:
    return CableState40(
        positions=prev.positions if prev else torch.zeros(40, 3),
        confidences=torch.zeros(40),
        stage_diagnostics={
            "fallback": reason,
            "total_latency_ms": (time.perf_counter() - t_start) * 1000.0,
        },
    )
```

### §3.4 Per-stage diagnostics aggregation (本 leaf 中核 contribution)

`CableState40.stage_diagnostics` は dict 型で freeze (parent §6.1 + types.py 既存)、本 leaf で schema を locking:

```python
stage_diagnostics: dict[str, Any] = {
    # Stage A.3 (Phase 1 substrate)
    "stage_a3": {
        "n_pts": int,                       # voxel-fused merged point count
        # Phase 5 で extend candidate: "n_pts_per_cam": list[int]
    },

    # Stage B (Phase 1 substrate)
    "stage_b": {
        "var_ratio": float,                 # SVD 1st singular value² ratio
        "bin_counts": list[int],            # [40] per-bin point count
        "L_est": float | None,              # estimated cable length (Phase 5 で expose)
    },

    # Stage C dispatcher result + per-stage detail
    "stage_c_triggered": bool,
    "stage_c": dict | None,                 # {"latency_ms": float} when triggered
                                            # Phase 5 で extend candidate:
                                            #   "fps_count": int (anchor sampling N)
                                            #   "input_warm_dist_mean": float (vs prev)

    # Stage D
    "stage_d": dict = {
        "final_loss": float,                # 7-term loss after fit
        "iter_count": int,                  # actual L-BFGS iter (vs max_iter=200)
        "restart_used": int,                # 0..4, which init was best
        "latency_ms": float,
        # Phase 5 で extend candidate:
        #   "loss_breakdown": dict[term, float]  # per-term contribution
        #   "convergence_reason": str  # "tol_grad" | "tol_change" | "max_iter"
    },

    # Identity inversion check
    "identity_inversion_detected": bool,    # § 3.5 Phase 2 spec

    # Stage E
    "stage_e": dict = {
        "latency_ms": float,
        # Phase 5 で extend candidate:
        #   "ece_estimate": float  # online ECE on calibration buffer
        #   "signal_means": dict[signal, float]  # debugging
    },

    # Total
    "total_latency_ms": float,

    # Failure-only fields
    "fallback": str | None,                 # set when Phase 1 fail (n_pts<800)
}
```

**Phase 6 (Q5 benchmark) consumption pattern**:
- per-scene aggregation: collect `stage_diagnostics` per scene → bench-side aggregator computes per-stage statistics (mean / p95 / fail rate)
- per-stage diagnostics threshold (parent §5.4) で warn / fail bucket 分類
- failure attribution: 逆引き failure mode に diagnostic を attach (例: "stage_d.iter_count == 200 + stage_d.final_loss > 5e-6" → Stage D timeout 帰属)

**downstream T-Vision-Fusion consumption pattern**:
- T-Vision-Fusion `EstimatorInputs.cable_state.confidences` を obs に fold-in (parent §6.4)
- diagnostics は inference path では consume せず、debug / monitoring path のみ

### §3.5 Backward compat policy

- `MultiCamCableStatePipeline.estimate()` (Phase 1 freeze): SOMA Stage 1-3 caller (single-midpoint use case) は Phase 5 で UNCHANGED 維持。Phase 5 で `estimate_with_cloud()` 新規 method 追加 (Phase 1 freeze 違反なし、既存 method UNCHANGED)
- `CableStatePhase1Result` (Phase 1 freeze): 本 leaf で UNCHANGED、Phase 5 で field 追加なし
- `EstimatorInputs` (Phase 1 で freeze): Phase 5 で UNCHANGED、cable_state inference 用 field は既存 (`rgb_oh` / `depth_oh` / `overhead_camera_pose` / `overhead_intrinsics` / `previous_cable_estimate`) で十分
- `CableStateCameraManager` (Phase 1 freeze): Phase 5 で UNCHANGED
- `CableStateSolver` (Phase 1 期 skeleton): Phase 5 で `__init__` + `_stage_*` body fill、API contract (`__call__` signature) は本 leaf §3.3 で locking
- 既存 `cable_state.py` `stage_a3_fuse_clouds` skeleton (Phase 1 期 起票): Phase 5 で impl OR delete (delete option: `vision_pipeline.voxel_downsample_points` に delegate)

---

## §4 Module boundary (R6 enforcement)

### §4.1 Per-file import policy

| file | allowed imports | forbidden imports |
|------|-----------------|-------------------|
| `estimators/cable_state.py` | `thread_isaac_lab.estimators.*` (types + cable_state_dd_pinn + cable_state_cosserat + cable_state_confidence)、`torch` | `newton`、`thread_isaac_lab.envs.*`、`thread_isaac_lab.configs.task_config` (constants は private mirror) |
| `estimators/cable_state_dd_pinn.py` | 同上 | 同上 |
| `estimators/cable_state_cosserat.py` | 同上 | 同上 |
| `estimators/cable_state_confidence.py` | 同上 + `sklearn.linear_model` (post-train calibration、optional) | 同上 |
| `estimators/types.py` | `torch` only | env / newton / configs |
| `models/vision_pipeline.py` | `numpy`, `torch`, `cv2` (HSV mask)、`thread_isaac_lab.envs.wrist_camera_manager` (CableStateCameraManager forward ref) | `newton` 直接 |
| `envs/wrist_camera_manager.py` | `torch`, `newton`, `thread_isaac_lab.configs.task_config` (env-side、newton import 許可) | (env-side、R6 制約外) |

### §4.2 Test plan (boundary tests)

**Phase 5 impl で拡張する既存 boundary tests**:

1. `tests/test_estimator_input_boundary.py` (Appendix D 名前 grep)
   - 既存: `EstimatorInputs` field name set が R6 spec に準拠
   - Phase 5 拡張: cable_state inference 用 field (`previous_cable_estimate` 等) も R6 boundary に含む

2. `tests/test_estimator_module_boundary.py` (`estimators/core/` AST lint)
   - 既存: `estimators/core/` 配下 newton import なし AST grep
   - Phase 5 拡張: `estimators/cable_state*.py` (`core/` 配下ではないが) 同 discipline self-enforce、AST grep 拡張

3. **新規 (Phase 5 起票時)**: `tests/test_cable_state_orchestrator.py`
   - `CableStateSolver.__call__` end-to-end synthetic test (straight + L + U + S shapes)
   - `_should_trigger_stage_c` defensive NaN handling
   - `stage_diagnostics` schema compliance (本 §3.4 spec 準拠)

### §4.3 R6 enforcement test extension spec for Phase 5

**Phase 5 起票時に追加する AST test pattern**:

```python
# tests/test_estimator_module_boundary.py に Phase 5 で追加 (本 Phase 3 では design only):
def test_cable_state_modules_no_newton():
    """R6 boundary: cable_state*.py modules must not import newton or envs."""
    target_files = [
        "thread_isaac_lab/estimators/cable_state.py",
        "thread_isaac_lab/estimators/cable_state_dd_pinn.py",
        "thread_isaac_lab/estimators/cable_state_cosserat.py",
        "thread_isaac_lab/estimators/cable_state_confidence.py",
    ]
    for fpath in target_files:
        with open(fpath) as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "newton" not in alias.name, f"{fpath} imports newton"
                    assert "thread_isaac_lab.envs" not in alias.name, f"{fpath} imports envs"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert "newton" not in node.module, f"{fpath} from-imports newton"
                    assert "thread_isaac_lab.envs" not in node.module, f"{fpath} from-imports envs"
```

**注**: 本 Phase 3 では Phase 2 skeleton smoke test (`test_cable_state_phase2_skeleton.py`) で per-module AST audit が既に存在する。Phase 5 impl 時に拡張、本 Phase 3 では reference のみ。

---

## §5 Q5 worst-case benchmark protocol (本 leaf 中核 contribution)

### §5.1 Eval dataset construction (parent §5.1 拡張)

#### §5.1.1 Scene composition (120 total)

| dataset | count | source | scenario | seed |
|---------|-------|--------|----------|------|
| Random clip routing | 100 | held-out 5-clip routing snapshots | random Phase / skill / cable shape | seed=42 |
| U-shape worst-case | 10 | scripted env (cable folding) | mid-cable folds back, 2 modes、varied fold positions × 2 fold-depth | seed=43 |
| S-shape worst-case | 10 | scripted env (2 inflection points) | 3 modes、varied insertion depths × clip combinations | seed=44 |

#### §5.1.2 Eval dataset generator function spec (Phase 6 impl reference)

```python
# Phase 6 で `tests/eval/generate_q5_eval_dataset.py` (新規 file、本 Phase 3 design only):
@dataclass
class Q5SceneSpec:
    """Single scene metadata for Q5 benchmark."""
    scene_id: str                              # "random_001", "ushape_005" etc.
    scene_type: str                            # "random" | "ushape" | "sshape"
    seed: int
    inputs: EstimatorInputs                     # rgb / depth / cam_poses / etc. dict (frozen)
    ground_truth: torch.Tensor                  # [40, 3] from env state dump
    scene_metadata: dict                        # {"phase": str, "cable_shape": str, etc.}

def generate_q5_eval_dataset(
    output_dir: Path,
    n_random: int = 100,
    n_ushape: int = 10,
    n_sshape: int = 10,
) -> list[Q5SceneSpec]:
    """Generate Q5 eval dataset (120 scenes total).

    Random scenes: sampled from 5-clip-routing held-out snapshots,
                   diversity across Phase / skill / cable shape.
    U-shape: scripted env scenarios with cable folding,
             varied fold positions (seg[15], seg[18], seg[20], seg[22], seg[25]) × 2 fold-depths.
    S-shape: scripted env scenarios with 2 inflection points,
             varied insertion depths × clip combinations.

    Args:
        output_dir: directory for serialized scenes (.pt files).
        n_random / n_ushape / n_sshape: scene counts per category.

    Returns:
        list of Q5SceneSpec (in order: random, ushape, sshape).
    """
    # Phase 6 impl:
    #   - Random sampling from held-out 5-clip routing replay
    #   - U-shape generation: scripted Newton env reset + grip mid-cable + pull back
    #   - S-shape generation: scripted Newton env routing through clip[1] + clip[3] grooves
    raise NotImplementedError("Phase 6 impl scope")
```

#### §5.1.3 U-shape scripted scenario detail

```
Step 1: Cable initially routed through clip[0], clip[1], clip[2] (Phase 5-3 baseline state)
Step 2: Robot grasps cable at mid-segment (e.g., seg[20])
        - varied fold positions: seg[15], seg[18], seg[20], seg[22], seg[25]
Step 3: Robot pulls grasp_pos toward back (z+0.05m, y-0.10m world)
        - varied fold-depth: medium (0.05m back), deep (0.10m back)
Step 4: Snapshot at fold-active frame (cable folded ~180°)
Expected: PCA var_ratio ≈ 0.4-0.5 (parent §2.3.3 既存 spec)
```

10 scene generation matrix: 5 fold positions × 2 fold-depths = 10 scenes (seed=43 + per-scene jitter)。

#### §5.1.4 S-shape scripted scenario detail

```
Step 1: Cable initially routed through clip[0], clip[1], clip[2], clip[3], clip[4]
Step 2: Insert cable into clip[1] groove (1st inflection)
Step 3: Insert cable into clip[3] groove (2nd inflection)
Step 4: Snapshot at inserted state (S-curve formed)
Expected: PCA var_ratio ≈ 0.3-0.4
```

10 scene generation matrix: 5 insertion depth combinations × 2 clip pair (clip[1]+clip[3] vs clip[0]+clip[2]) = 10 scenes (seed=44 + per-scene jitter)。

#### §5.1.5 Random scene specification (parent §5.1.2 直引き)

- sample from current 5-clip-routing dataset (P-state + skill execution snapshots)
- ensure diversity across:
  - Phase ∈ {approach, grip, lift, transport, insert, release}
  - skill mid-execution states (no end-of-episode bias)
  - cable shape variety (straight 50%, bent 30%, complex 20%)
- random seed fixed for reproducibility (seed=42 for 100 scenes)

### §5.2 Per-scene evaluation function spec (Phase 6 impl reference)

```python
@dataclass
class Q5SceneMetrics:
    """Single scene evaluation result."""
    scene_id: str
    scene_type: str

    # Primary error metrics
    mean_error_m: float                # ē = mean per-segment error
    p95_error_m: float                  # 95th percentile per-segment error
    max_error_m: float                  # max per-segment error

    # Topology
    identity_inversion: bool            # check_inversion(P̂_seg, GT)
    has_nan_segments: bool              # any NaN in P̂_seg

    # Confidence calibration (per-scene contribution to ECE)
    per_seg_errors: torch.Tensor        # [40] all per-segment errors (for global ECE)
    per_seg_confidences: torch.Tensor   # [40] all confidences

    # Latency
    total_latency_ms: float

    # Per-stage diagnostics (full pass-through from CableStateSolver)
    stage_diagnostics: dict             # § 3.4 schema

def evaluate_scene(
    estimator: "CableStateSolver",
    pipeline: "MultiCamCableStatePipeline",
    scene: Q5SceneSpec,
) -> Q5SceneMetrics:
    """Evaluate single scene end-to-end.

    Phase 6 impl:
      1. Run pipeline.estimate_with_cloud(scene.inputs.finger_positions, prev=None) → (phase1_result, cloud)
      2. Run estimator(cloud, phase1_result, prev=None, finger_positions=scene.inputs.finger_positions) → CableState40
      3. Compute per-segment errors: e_per_seg = ‖P̂_seg - scene.ground_truth‖₂ ∈ [40]
      4. Compute identity inversion: check P̂_seg(0) vs grasp_finger anchor
      5. Aggregate metrics dataclass
    """
    raise NotImplementedError("Phase 6 impl scope")

def check_identity_inversion(
    seg_estimated: torch.Tensor,        # [40, 3]
    seg_gt: torch.Tensor,                # [40, 3]
    threshold_m: float = 0.05,
) -> bool:
    """Identity inversion: P̂_seg(0) maps to GT seg(39) or vice versa.

    Phase 6 impl:
      - dist_normal = ‖P̂_seg - seg_gt‖₂.mean()
      - dist_reversed = ‖P̂_seg - flip(seg_gt)‖₂.mean()
      - if dist_reversed + threshold_m < dist_normal: return True
      - else: return False
    """
    raise NotImplementedError("Phase 6 impl scope")
```

### §5.3 PASS criteria evaluator (parent §5.3 拡張)

```python
@dataclass
class Q5BenchVerdict:
    """Q5 gate PASS / FAIL verdict."""
    overall_passed: bool
    per_gate_status: dict[str, bool]    # gate_name → passed

    # Detailed
    random_mean_error_m: float
    random_p95_error_m: float
    ushape_mean_errors_m: list[float]    # per-scene means [10]
    sshape_mean_errors_m: list[float]    # per-scene means [10]
    identity_inversion_count: int        # /120 total
    overall_ece: float
    latency_p95_ms: float

def evaluate_q5_gate(per_scene_metrics: list[Q5SceneMetrics]) -> Q5BenchVerdict:
    """Aggregate per-scene metrics into Q5 gate verdict.

    PASS criteria (parent §5.3 既存 + 本 Phase 3 で gate name lock):
    """
    random_metrics = [m for m in per_scene_metrics if m.scene_type == "random"]
    ushape_metrics = [m for m in per_scene_metrics if m.scene_type == "ushape"]
    sshape_metrics = [m for m in per_scene_metrics if m.scene_type == "sshape"]

    gates = {}

    # Gate 1: Random N=100 mean(ē) < 5mm
    gates["random_mean_error_lt_5mm"] = (
        sum(m.mean_error_m for m in random_metrics) / len(random_metrics) < 0.005
    )

    # Gate 2: Random N=100 mean(e_p95) < 10mm
    gates["random_p95_error_lt_10mm"] = (
        sum(m.p95_error_m for m in random_metrics) / len(random_metrics) < 0.010
    )

    # Gate 3: U-shape 10/10 ē < 5mm each (individual scene compliance)
    gates["ushape_all_lt_5mm"] = all(m.mean_error_m < 0.005 for m in ushape_metrics)

    # Gate 4: S-shape 10/10 ē < 5mm each
    gates["sshape_all_lt_5mm"] = all(m.mean_error_m < 0.005 for m in sshape_metrics)

    # Gate 5: Identity inversion rate 0% (all 120)
    gates["zero_identity_inversion"] = all(
        not m.identity_inversion for m in per_scene_metrics
    )

    # Gate 6: Confidence ECE < 5%
    overall_ece = compute_global_ece(per_scene_metrics)
    gates["ece_lt_5pct"] = overall_ece < 0.05

    # Gate 7: Latency P95 < 50ms
    all_latencies = sorted(m.total_latency_ms for m in per_scene_metrics)
    p95_idx = int(0.95 * len(all_latencies))
    gates["latency_p95_lt_50ms"] = all_latencies[p95_idx] < 50.0

    return Q5BenchVerdict(
        overall_passed=all(gates.values()),
        per_gate_status=gates,
        # ... details
    )
```

**Gate decision rule**: 7 gates 全 PASS で overall_passed=True。1 gate でも FAIL → Q5 gate FAIL、failure attribution は per-stage diagnostics aggregator (§5.4) で実施。

### §5.4 Per-stage diagnostics aggregator (parent §5.4 拡張)

```python
@dataclass
class Q5StageDiagnosticsReport:
    """Per-stage failure attribution report."""
    stage: str                            # "A" | "B" | "C" | "D" | "E" | "Identity"
    metric_name: str
    threshold_warn: float
    threshold_fail: float
    n_warn: int                           # count of scenes in warn range
    n_fail: int                           # count of scenes in fail range
    examples_fail: list[str]              # scene_ids that failed (top 5)

PER_STAGE_THRESHOLDS = {
    # parent §5.4 直引き
    "A_n_pts": {"warn": 1500, "fail": 800, "direction": "below"},  # below threshold = bad
    "A_per_cam_iou": {"warn": 0.85, "fail": 0.70, "direction": "below"},  # MVP-0B v2 ready 後
    "B_var_ratio_random": {"warn": 0.7, "fail": 0.6, "direction": "below"},  # random scene のみ
    "B_bin_emptiness": {"warn": 4, "fail": 8, "direction": "above"},
    "C_warm_mse": {"warn": 0.008, "fail": 0.015, "direction": "above"},
    "C_latency": {"warn": 0.003, "fail": 0.005, "direction": "above"},  # seconds
    "D_residual": {"warn": 0.002, "fail": 0.005, "direction": "above"},  # meters
    "D_iter_count": {"warn": 150, "fail": 200, "direction": "above"},
    "E_ece": {"warn": 0.05, "fail": 0.10, "direction": "above"},
    "Total_latency": {"warn": 0.05, "fail": 0.10, "direction": "above"},  # seconds
}

def aggregate_stage_diagnostics(
    per_scene_metrics: list[Q5SceneMetrics],
) -> list[Q5StageDiagnosticsReport]:
    """Generate per-stage failure attribution report from per-scene diagnostics dicts."""
    # Phase 6 impl:
    #   for each (metric_key, thresh) in PER_STAGE_THRESHOLDS:
    #     extract metric per scene, count warn/fail scenes, attach scene_ids
    raise NotImplementedError("Phase 6 impl scope")
```

### §5.5 Eval pipeline orchestration (Phase 6 reference)

```python
def run_q5_benchmark(
    pipeline: "MultiCamCableStatePipeline",
    estimator: "CableStateSolver",
    eval_dataset: list[Q5SceneSpec],
    output_dir: Path,
) -> tuple[Q5BenchVerdict, list[Q5StageDiagnosticsReport]]:
    """End-to-end Q5 benchmark execution. Phase 6 impl scope."""
    per_scene_metrics = [evaluate_scene(estimator, pipeline, scene) for scene in eval_dataset]
    verdict = evaluate_q5_gate(per_scene_metrics)
    stage_reports = aggregate_stage_diagnostics(per_scene_metrics)

    # Output artifacts:
    #   - q5_verdict.json: Q5BenchVerdict serialized
    #   - q5_stage_diagnostics.json: stage_reports serialized
    #   - q5_per_scene_metrics.parquet: full per-scene metrics for downstream analysis
    #   - q5_summary.md: human-readable report
    return verdict, stage_reports
```

---

## §6 Latency budget (per-stage + total)

### §6.1 Per-stage allocation (parent §2.5.3 + §5.4 reference)

| stage | budget | typical (warm start 経) | rationale |
|-------|--------|-------------------------|-----------|
| Stage A.3 voxel fusion | 5ms | 3-5ms | numpy `np.unique` O(N log N) at N~3000 |
| Stage B PCA + 40-bin | 5ms | 2-3ms | torch SVD O(N×3) + bin sum O(N) |
| Stage C DD-PINN (when triggered) | 2ms | 1-2ms | small MLP (~54k params) inference + FPS sampling |
| Stage D Cosserat fit | 30ms | 20-30ms | warm start で 30-50 iter × 0.5-1ms/iter (PyTorch L-BFGS) |
| Identity inversion check | 3ms | 1-3ms | conditional 1-pass refit (when detected、not always) |
| Stage E confidence | 5ms | 2-5ms | signals computation + sigmoid aggregation |
| **Total** | **50ms** | **30-40ms** | parent §5.3 PASS criteria threshold |

### §6.2 Multi-restart parallelization

Stage D 5-restart × 30ms = 150ms (sequential、超過)。Phase 5 で parallel batch 化検討:
- Option A: `torch.vmap` で 5-restart 並列 (PyTorch 2.0+)、batched LBFGS state
- Option B: 5 restart sequential、batch dim 1 (Phase 5 impl 簡素化)
- Option C: Warp kernel 化 (Phase 7 別 leaf)

**Phase 5 採択 (本 Phase 3 推奨)**: Option A 試行、PyTorch native 不可なら Option B fallback。Phase 6 latency profile 経で empirical revision。

### §6.3 Latency budget overrun mitigation chain

```
Phase 6 Q5 latency p95 measurement:
  if total < 50ms (PASS):
    finalize Phase 5 PyTorch L-BFGS impl
  elif 50ms ≤ total < 100ms (WARN):
    investigate per-stage breakdown:
      - Stage D > 30ms → reduce max_iter (200→100), reduce restart_count (5→3)
      - Stage C > 2ms → reduce n_anchor (256→128) per OQ-P2-2
    re-profile, repeat
  elif total ≥ 100ms (FAIL):
    Phase 7 起票候補 (Warp kernel):
      - CosseratWarpSolver (batched 7-term loss + KD-tree NN)
      - estimated speedup ~10x → total ~10ms expected
```

---

## §7 Failure mode tabulation (parent §5.5 拡張)

| F | mode | symptom | mitigation chain |
|---|------|---------|------------------|
| F1 | HSV mask drift (lighting / texture) | Stage A mIoU drops、cloud sparse | MVP-0B v2 9-class seg (T-Vision-Pose 範囲) + DR Tier 0 D1-D2 + 9-class swap when mIoU≥0.85 |
| F2 | Depth dropout (specular surface) | sparse cloud regions、Stage B var_ratio drops | DR Tier 0 D5 (sensor noise + dropout train) + Stage A.3 voxel dedupe + Stage D L_temp |
| F3 | Self-occlusion (cable under cable) | some segs no points、bin emptiness | Stage A.3 multi-cam fusion + Stage D L_temp + Stage C warm start (DD-PINN trained on 500 U/S) |
| F4 | PCA fail (U/S shape) | var_ratio < 0.6 | Designed: Stage C DD-PINN trigger + Stage D 7-term loss multi-mode handling |
| F5 | Cosserat local minima | L tail > 5mm after 100 iter | Multi-restart (5×σ=2mm) + Stage C re-init + best-L selection |
| F6 | Identity inversion (parent §3.3) | P_seg(0) vs P_seg(39) flip | Identity inversion check (Stage D 内 1-pass refit) + L_id anchor (grasp finger Tier 1) |
| F7 | Latency overflow | total > 50ms | Warm start reduces Stage D iter; profile + tune; Phase 7 Warp kernel 候補 |
| F8 | NaN segment propagation | gradient explosion in Stage D | mask_valid handling (本 §2.3) + smoke test で NaN reach 確認 |
| F9 | Cloud expose API gap (Phase 1 → Phase 2) | Phase 5 で env-side wrapper 実装漏れ | 本 §2.2 で adapter spec lock (option (b))、Phase 5 で `MultiCamCableStatePipeline.estimate_with_cloud()` 新規 method 追加 (Phase 1 freeze 維持) |
| F10 | Stage C checkpoint missing | DD-PINN forward fail at runtime | `CableStateSolver.__init__` で checkpoint validity check + raise RuntimeError if absent (本 §3.2 invariant) |
| F11 | Phase 番号 renumber 混乱 (Phase 2 memo "Phase 3 = Stage C train" vs 本 leaf "Phase 3 = Integration Design") | Phase 4 起票時 spec source 不明 | 本 §1.4 + state.md §1 + manifest §運用注 で永続化 |
| F12 | per-stage diagnostics schema drift | Phase 6 bench-side aggregator が consume できない | 本 §3.4 で schema lock、Phase 5 impl 時に `tests/test_cable_state_orchestrator.py` で schema compliance enforce |

---

## §8 Phase 4-6 trigger spec + dependency cascade

### §8.1 Phase 4 (Stage C train) 起票 trigger

| precondition | mechanism | external dependency |
|--------------|-----------|---------------------|
| 本 Phase 3 design memo COMPLETE | leaf state.md status COMPLETE 経 | (本 leaf 完走) |
| 5k labeled dataset generation infrastructure ready | T-Vision-DR-Impl-Phase0-PrepDesign cascade (Tier 0 sim labeled scenes) | T-Vision-DR-Impl-Phase0 完走 + dataset render pipeline ready |
| ~25h GPU 確保 (cuda:2 deterministic kernel、4-process limit) | GPU schedule + prior process cleanup | 他 cuda:2 使用 task との conflict 解消 |
| Rs §3.1 #4 起動承認 | 別 NEST node `T-Vision-CableState-Impl-Phase-4-Stage-C-Train` 起票時の Rs explicit approve | (Rs availability) |

**spec source**: 本 design memo §3 (orchestration pattern)、§5 (Q5 benchmark protocol、Phase 6 起票時 spec source)、Phase 2 memo §2.2 (training pipeline spec)。

### §8.2 Phase 5 (Stage D/E impl) 起票 trigger

| precondition | mechanism | external dependency |
|--------------|-----------|---------------------|
| Phase 4 PASS (Stage C MSE < 8mm warm start) | Phase 4 leaf state.md status COMPLETE + Phase 5.4 per-stage diagnostics PASS | Phase 4 完走 + DD-PINN checkpoint 生成 |
| PyTorch L-BFGS / Warp kernel infrastructure ready | (PyTorch L-BFGS は existing torch.optim.LBFGS、追加準備不要; Warp kernel は Phase 7 defer 想定) | (immediate) |
| 1k val held-out 整備済 | T-Vision-DR-Impl-Phase0 cascade (4k train + 1k val split) | dataset render 完了 |
| `cable_state.py` `CableStateSolver` orchestrator delegate 接続 | Phase 5 impl: 本 design memo §3 の orchestration pattern を impl 経 | (本 design memo を spec source として Phase 5 で reference) |

**spec source**: 本 design memo §3 (orchestrator)、Phase 2 memo §2.3 (Stage C class skeleton)、§3.7 (Stage D class skeleton)、§4.5 (Stage E class skeleton)。

### §8.3 Phase 6 (Q5 benchmark execution) 起票 trigger

| precondition | mechanism | external dependency |
|--------------|-----------|---------------------|
| Phase 5 COMPLETE | Phase 5 leaf state.md status COMPLETE | (Phase 5 完走) |
| 10 U + 10 S scripted scene generator ready | env-side scripted scenarios impl (本 §5.1.3 + §5.1.4 spec 経で newton env scripting) | env-side eng (~3-5h) |
| N=100 random held-out scenes generation | env-side replay sampling impl (本 §5.1.5 spec) | (immediate、existing replay infrastructure 経) |
| Q5 gate execution + ECE measurement + identity inversion 0% verify + latency p95 <50ms verify | 本 §5 spec を impl 経で実行 | (本 design memo を spec source として Phase 6 で reference) |

**spec source**: 本 design memo §5 全 (Q5 benchmark protocol)。

### §8.4 Dependency cascade visualization

```
T-Vision-CableState-Impl-Phase-3-Integration-Design (本 leaf)
  │
  │  ↓ design spec source
  │
  ├── Phase 4 起票 trigger (5k dataset + 25h GPU + Rs)
  │     T-Vision-CableState-Impl-Phase-4-Stage-C-Train
  │       │ ↓ Stage C checkpoint
  │       │
  │       ├── Phase 5 起票 trigger (Phase 4 PASS + 1k val + cable_state.py orchestrator)
  │       │     T-Vision-CableState-Impl-Phase-5-Stage-DE
  │       │       │ ↓ Stage D + E impl + cable_state.py CableStateSolver delegate fill
  │       │       │
  │       │       └── Phase 6 起票 trigger (Phase 5 COMPLETE + scripted scenes ready)
  │       │             T-Vision-CableState-Impl-Phase-6-Q5-Bench
  │       │               │ ↓ Q5 verdict
  │       │               │
  │       │               └── (Phase 7 起票 trigger: latency p95 ≥100ms 観察 経)
  │       │                     T-Vision-CableState-Impl-Phase-7-Warp (候補)
  │       │
  │       └── (T-Vision-DR-Impl-Phase0 cascade, T-Vision-Pose MVP-0B v2 unblock cascade)
  │
  └── Phase 6 完走 経で T-Vision-CableState (parent) Q5 gate PASS judgment
        T-Vision-CableState status: IN_PROGRESS → COMPLETE
```

---

## §9 Risk register (Phase 3 specific)

| ID | risk | severity | likelihood | mitigation |
|----|------|----------|------------|------------|
| P3-R1 | design memo が parent memo §6 + Phase 2 memo §5 と重複 (value add 不足) | MED | LOW | 本 leaf §3 (file ownership matrix + orchestration code spec)、§5 (Q5 benchmark eval pipeline implementation-ready)、§6 (latency budget per-stage)、§7 (F8-F12 拡張 failure modes) で差別化 |
| P3-R2 | Phase 1 → Phase 2 cloud propagation API gap (本 §2.2 F9) | HIGH | LOW | 本 §2.2 で adapter spec option (b) lock、Phase 5 impl 時に `estimate_with_cloud()` 新規 method 追加 (Phase 1 freeze 維持) |
| P3-R3 | per-stage diagnostics schema が Phase 6 bench-side で consume できない | HIGH | LOW | 本 §3.4 で schema lock、Phase 5 impl 時 `tests/test_cable_state_orchestrator.py` で schema compliance enforce |
| P3-R4 | Q5 benchmark protocol が parent §5 と implementation-ready 度合いで gap | MED | LOW | 本 §5 で eval dataset generator + per-scene metric + PASS criteria evaluator + diagnostics aggregator の 4 要素 spec、Phase 6 起票時の boilerplate elimination |
| P3-R5 | latency budget 50ms 内 per-stage 配分が non-feasible | MED | MED | 本 §6 で per-stage budget table + warm start reduction estimate + multi-restart parallel 化 + Phase 7 Warp kernel 化 mitigation chain spec |
| P3-R6 | Phase 番号 renumber 混乱 (本 §1.4 F11) | MED | MED | 本 §1.4 + state.md §1 + manifest §運用注 paragraph で永続化 |
| P3-R7 | TOUCH FORBIDDEN 違反 (本 leaf で誤って既存 .py file 改変) | HIGH | LOW | 本 leaf 完走時 `git diff --name-only` で改変ファイル列挙 + 本 §1 + state.md §4 「TOUCH FORBIDDEN」 list と照合 (機械的検証、§運用15 層3) |
| P3-R8 | identity inversion check が Stage D 内 1-pass refit で不十分 (Phase 6 で 0% target 未達) | MED | MED | 本 §3.3 で `_verify_identity` invocation spec lock、Phase 6 で empirical 0% verify、未達時 anchor source priority 拡張 (parent §3.5 Tier 2 prev_estimate fold-in candidate) |
| P3-R9 | NaN handling end-to-end (本 §2.3) が連続 NaN 5+ で gradient explosion | HIGH | LOW | 本 §2.3 で stage-per-stage mask_valid spec lock、Phase 5 impl 時 `tests/test_cable_state_orchestrator.py` で synthetic NaN reach test |
| P3-R10 | Phase 4-6 起票 trigger cascade が並行 conflict (例: 5k dataset 生成 と Phase 5 impl 並行で GPU 競合) | LOW | MED | 本 §8 で trigger spec lock、各 Phase 起票時 Rs explicit GPU schedule confirmation |

---

## §10 Open questions (Phase 4+ revision trigger)

| OQ | topic | Phase 3 disposition | trigger for revision |
|----|-------|---------------------|----------------------|
| OQ-P3-1 | `CableStateSolver` orchestrator delegate pattern (constructor inject vs sub-module 経 wrapper) | constructor inject 推奨 (本 §3.2)、parent §6.2 reference pattern 整合 | Phase 5 impl 時 multiple instance reuse / DI complexity 観察 |
| OQ-P3-2 | Stage B var_ratio threshold 0.6 hard-code vs configurable | configurable (本 §2.4、`CableStateSolverConfig.var_ratio_threshold = 0.6` default) | Phase 6 Q5 で 0.5-0.7 sweep 観察 |
| OQ-P3-3 | Q5 benchmark eval dataset の random seed | seed=42 (parent §5.1.2 既存)、Phase 6 で reproducibility 確認 | Phase 6 で reproducibility issue 観察 |
| OQ-P3-4 | per-stage diagnostics output format (dict vs dataclass) | dict (parent §6.1 + types.py 既存 freeze) | Phase 5 impl で type safety 観察 |
| OQ-P3-5 | identity inversion check の Stage D 内 1-pass refit vs Stage E への delegation | Stage D 内 1-pass refit (Phase 2 §3.5 既存 spec、本 §3.3 踏襲) | Phase 5 impl で latency 観察 |
| OQ-P3-6 | latency budget 50ms の per-stage 配分 | A:5 / B:5 / C:2 / D:30 / E:5 / Identity:3 = 50ms (本 §6.1) | Phase 6 Q5 latency profile 経 |
| OQ-P3-7 | 5k labeled dataset の sampling spec coverage | parent §5.1.2 + §2.4.3 直引き、4k random + 500 U + 500 S | Phase 4 train 時 dataset coverage gap 観察 |
| OQ-P3-8 | Phase 1 → Phase 2 cloud propagation API (adapter option a / b / c) | option (b) env-side wrapper inject (本 §2.2) | Phase 5 impl で wrapper complexity 観察 |
| OQ-P3-9 | Stage D multi-restart parallelization (Option A vmap / B sequential / C Warp) | Option A vmap 試行、不可なら Option B fallback (本 §6.2) | Phase 5 impl で torch.vmap LBFGS state batching 観察、Phase 6 latency 経で Option C decision |
| OQ-P3-10 | NaN segment 連続 5+ 時の Stage C trigger 拡張 | 現 condition (var_ratio < 0.6) 維持、Phase 6 で empirical revise (本 §2.3) | Phase 6 連続 NaN 観察時 Stage C trigger condition 拡張 (`var_ratio < 0.6 OR consecutive_nan ≥ 5`) |
| OQ-P3-11 | `cable_state.py` 既存 `stage_a3_fuse_clouds` skeleton vs `vision_pipeline.voxel_downsample_points` の重複 | Phase 5 impl 時 delegate to vision_pipeline 推奨 (本 §3.1 file ownership matrix) | Phase 5 impl で API ergonomics 観察 |

---

## §11 Cross-references

### §11.1 Internal vault

- **Parent design memo**: `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md` (769 行、approved 2026-05-03、§2 + §3 + §5 + §6 spec source)
- **Sibling Phase 2 design memo**: `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase2-Impl-Design.md` (~820 行、design 2026-05-04、§2 (Stage C) + §3 (Stage D) + §4 (Stage E) + §5 (Phase 1 → Phase 2 component-level integration) spec source)
- **Sibling Phase 1 state**: `thread_isaac_lab/thread-vault/T-Vision-CableState-Impl-Phase-1/state.md` (COMPLETE 2026-05-04T03:50)
- **Sibling Phase 2 state**: `thread_isaac_lab/thread-vault/T-Vision-CableState-Impl-Phase-2-Design/state.md`
- **Parent NEST node**: `thread_isaac_lab/thread-vault/T-Vision-CableState/state.md`
- **CC4 v3.2 base spec**: `thread_isaac_lab/thread-vault/07-Design/PoseEstimation-Design-v3.2.md` §H Estimator boundary、§5.4 Stage 3a expand、§6.4 Late Fusion downstream
- **R6 boundary tests**: `thread_isaac_lab/tests/test_estimator_input_boundary.py` + `tests/test_estimator_module_boundary.py` + `tests/test_cable_state_phase1.py` + `tests/test_cable_state_phase2_skeleton.py`

### §11.2 Code references

- `thread_isaac_lab/configs/task_config.py:70-75` (CABLE_SEGMENTS=40, CABLE_SEG_LEN=0.015, CABLE_BEND_STIFFNESS=0.1) — TOUCH FORBIDDEN、private constant mirror in `cable_state.py` で R6 self-enforce
- `thread_isaac_lab/models/vision_pipeline.py` (Phase 1 完成 `MultiCamCableStatePipeline` + `CableStatePhase1Result`、L406-727) — TOUCH FORBIDDEN、Phase 5 で `estimate_with_cloud()` 新規 method 追加 (既存 freeze 維持、本 §2.2 option (b) spec)
- `thread_isaac_lab/envs/wrist_camera_manager.py` (Phase 1 完成 `CableStateCameraManager` + overhead world-fixed cam) — TOUCH FORBIDDEN
- `thread_isaac_lab/estimators/types.py` (Phase 1 freeze `CableState40` + `EstimatorInputs` Phase 2 fields) — TOUCH FORBIDDEN
- `thread_isaac_lab/estimators/cable_state.py` (既存 `CableStateSolver` skeleton、L136-345) — Phase 5 impl scope (本 §3 orchestration pattern を impl)、本 Phase 3 では reference のみ
- `thread_isaac_lab/estimators/cable_state_dd_pinn.py` (Phase 2 skeleton freeze) — Phase 5 で forward + checkpoint loading impl、本 Phase 3 では reference のみ
- `thread_isaac_lab/estimators/cable_state_cosserat.py` (Phase 2 skeleton freeze) — Phase 5 で fit + _compute_loss + _verify_identity impl、本 Phase 3 では reference のみ
- `thread_isaac_lab/estimators/cable_state_confidence.py` (Phase 2 skeleton freeze) — Phase 5 で compute_signals + aggregate + LogisticCalibrator + compute_ece impl、本 Phase 3 では reference のみ
- `thread_isaac_lab/estimators/aggregator.py`、`thread_isaac_lab/estimators/input_adapter.py` — Phase 5 で extend candidate (env-side wrapper)、本 Phase 3 では reference のみ

### §11.3 Sister leaves & downstream

- **T-Vision-CableState** (parent umbrella、design APPROVED + Phase 1 COMPLETE + Phase 2 design COMPLETE)
- **T-Vision-Pose** (sister precedent for Stage A-B substrate、APPROVED_FOR_IMPL)
- **T-Vision-DR** (sister、shared dataset re-render asset、Tier 0 ~10h GPU、Phase 4 dataset prerequisite cascade)
- **T-Vision-Fusion** (downstream consumer、cable_state 120D obs 統合、L1.A.4 = Phase 5-4 G8)、`EstimatorInputs.cable_state` 経で confidence + positions consume

### §11.4 Future Phase 4-6 trigger spec (本 §8 別 detail)

- Phase 4 (Stage C train): 5k dataset + ~25h GPU + Rs §3.1 #4 経で起票 (本 §8.1)
- Phase 5 (Stage D/E impl): Phase 4 PASS + 1k val + cable_state.py orchestrator delegate 経で起票 (本 §8.2)
- Phase 6 (Q5 benchmark execution): Phase 5 COMPLETE + scripted scene generator + N=100 random sampling 経で起票 (本 §8.3)
- Phase 7 (Warp kernel optimization、候補): Phase 6 latency p95 ≥100ms 観察時起票 (本 §6.3)

---

## §12 Status

- **Created:** 2026-05-04T05:05:00 (T-Vision-CableState-Impl-Phase-3-Integration-Design-CC sub-session)
- **Phase:** design (impl + train + benchmark execution pending、Phase 4-6 別 NEST node)
- **Author:** T-Vision-CableState-Impl-Phase-3-Integration-Design-CC (sub-agent of T-ROOT-COORD#s11)
- **Permissions:** 06-Knowledge は CC Create/Update 可 (Vault Write Permissions)
- **Authority:** L0 Rs proxy approve (`feedback_autonomous_full_authority_2026-05-03` 3-step expansion、Wk:45%)
- **Next steps (Phase 4 trigger)**:
  - 本 Phase 3 design + state.md + manifest + Tier 2 + memory entry COMPLETE
  - 5k labeled dataset generation infrastructure ready (T-Vision-DR-Impl-Phase0 cascade)
  - cuda:2 ~25h GPU schedule 確認
  - Rs §3.1 #4 起動承認

---

## §13 Output format compliance (CLAUDE.md §運用)

| 区分 | 主張 | 根拠（出典） |
|------|------|-------------|
| 事実 | parent memo §6.1 で `CableState40` dataclass spec (positions [B, 40, 3] + confidences [B, 40] + stage_diagnostics: dict) | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md:557-563` |
| 事実 | parent memo §6.2 で `CableStateSolver.__init__(dd_pinn, cosserat_kernel, config)` 経 + `__call__(cloud, prev) → CableState40` interface spec | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md:594-625` |
| 事実 | Phase 2 memo §5.1 で Phase 1 → Phase 2 data flow + var_ratio gate (< 0.6 trigger Stage C) + identity inversion check (Stage D 内 1-pass refit) spec | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase2-Impl-Design.md:589-617` |
| 事実 | Phase 1 完成 `CableStatePhase1Result` 6 field (seg_positions / bin_counts / var_ratio / n_pts / fallback_reason / succeeded) | `thread_isaac_lab/thread-vault/T-Vision-CableState-Impl-Phase-1/state.md:5` (goal_verification 経) |
| 事実 | 既存 `CableStateSolver` skeleton at `cable_state.py` L136-345 with `_stage_b/c/d/e` raising NotImplementedError + `CableStateSolverConfig` defaults (var_ratio_threshold=0.6, voxel_size_m=0.002, n_pts_min_gate=800, cosserat_max_iter=200, identity_inversion_delta_m=0.05, weights={...}) | `thread_isaac_lab/estimators/cable_state.py:76-103` (CableStateSolverConfig) + 同 file L136-345 (CableStateSolver) |
| 事実 | parent memo §5.3 で 7 PASS gate spec (random mean<5mm + p95<10mm + U/S 10/10 each<5mm + identity inv 0% + ECE<5% + latency p95<50ms) | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md:509-518` |
| 事実 | parent memo §5.4 per-stage diagnostics warn / fail thresholds (A_n_pts warn<1500/fail<800、B_var_ratio warn<0.7/fail<0.6、Total latency warn>50ms/fail>100ms 等) | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md:520-532` |
| 事実 | Phase 2 memo Stage D PyTorch L-BFGS first 推奨 (autograd 完全 + dev cost 圧縮、Warp 化は Phase 5 latency profile 経で defer) | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase2-Impl-Design.md:312-323` |
| 推測 | Phase 1 → Phase 2 cloud propagation で option (b) env-side wrapper inject が Phase 1 freeze 維持 + adapter complexity 最小 | option (a) re-derive ~5ms overhead + option (c) Phase 1 freeze 違反 vs option (b) wrapper +1 method の trade-off。Phase 5 impl で empirical revise 可能 (本 §10 OQ-P3-8) |
| 推測 | per-stage latency budget A:5/B:5/C:2/D:30/E:5/Identity:3 = 50ms total 達成可能 (warm start 経で typical 30-40ms) | parent §2.5.3 "warm start 経で 30-50 iter 収束 → 5-10ms" + Phase 2 §3.6 "5-restart × 60ms = 300ms (parallel 化候補 → ~60ms)" 引用、本 §6 で multi-restart parallel + Phase 7 Warp kernel mitigation chain 経 |
| 推測 | Q5 benchmark protocol implementation-ready level の本 §5 spec で Phase 6 boilerplate elimination (起票時 ~3-5h 圧縮見込み) | T-Vision-DR-Impl-Phase0-PrepDesign + T-Vision-Fusion-Impl-Phase-1-Architecture-Design 同 pattern (~4-6h 圧縮見込み) の precedent 経 |
| 推測 | Phase 番号 renumber 経で Phase 2 memo §9.4 trigger spec が永続的に整合性確保 | 本 §1.4 + state.md §1 + manifest §運用注 paragraph 三重防御で renumber 公示、precedent T-WM-G2-A4 → A5/A7 rename pattern 経 |
