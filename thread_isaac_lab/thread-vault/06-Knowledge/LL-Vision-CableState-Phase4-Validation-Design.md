---
title: Cable State Estimation Phase 4 Validation Design (validation methodology + benchmark protocol final)
created: '2026-05-04T14:05:00+09:00'
tags:
  - knowledge
  - vision
  - cable-state
  - phase-4-validation-design
  - design-reference
status: design (T-Vision-CableState-Impl-Phase-4-Validation-Design-CC、Phase 4 = validation methodology + Q5 benchmark protocol final scope only、impl + train + benchmark execution は Phase 5-7 別 NEST node)
node_id: T-Vision-CableState-Impl-Phase-4-Validation-Design
session: T-Vision-CableState-Impl-Phase-4-Validation-Design-CC
parent_memo: thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md
sibling_memo: thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase3-Integration-Design.md
doc_class: design-surface
---

# LL-Vision-CableState-Phase4-Validation-Design

> T-Vision-CableState 5-stage pipeline (Hybrid PCA + Cosserat) **Phase 4 validation methodology + benchmark protocol final design** memo。Phase 3 (Stages A-E end-to-end integration design + Q5 benchmark protocol initial spec) §5 を implementation-ready level に finalize、Phase 5 (Stage C train) → Phase 6 (Stage D/E impl) → Phase 7 (Q5 benchmark execution) の eval pipeline を boilerplate elimination 経で起票時 spec source として機能。
>
> **scope:** design only。impl + train + benchmark execution は Phase 5 (Stage C train、~25h GPU) / Phase 6 (Stage D/E impl) / Phase 7 (Q5 benchmark execution) で起票。
>
> **base:** parent memo §1 (target metric)、§5 (benchmark spec); Phase 3 memo §5 (Q5 benchmark protocol initial)、§7 (failure mode F1-F12)、§6 (latency budget)、§3 (per-stage diagnostics schema)。
>
> **boundary:** R6 input-boundary 遵守。本 leaf は doc-only、`cable_state.py` / `vision_pipeline.py` / `wrist_camera_manager.py` / `cable_state_*.py` skeletons / `task_config.py` / `04-Specs/*.md` / `types.py` / `tests/test_cable_state_*.py` 全 TOUCH FORBIDDEN。

---

## §0 Executive summary

- **Phase 4 = validation methodology + Q5 benchmark protocol final design** scope。本 memo の deliverable は doc-only、code 改変なし。Phase 5-7 起票時の spec source として機能。
- **Per-section ownership matrix vs Phase 3 §5** (本 leaf 中核 differentiation):
  - Phase 3 §5.1 (scene generation skeleton) → 本 §2 (scene generation finalized impl + per-scene jitter spec + scene metadata schema)
  - Phase 3 §5.2 (per-scene metric skeleton) → 本 §4 (per-scene metric impl-ready + return type freeze + downstream consumption)
  - Phase 3 §5.3 (PASS criteria skeleton) → 本 §5 (7 gates final + per-gate rationale + tie-breaking + edge case handling)
  - Phase 3 §5.4 (diagnostics aggregator skeleton) → 本 §6 (10 thresholds final + threshold revision pathway + Q5StageDiagnosticsReport finalization)
  - Phase 3 §5.5 (eval pipeline skeleton) → 本 §10 (reporting format spec: CSV + JSON + summary md)
  - **NEW (Phase 3 で skeleton 不在)**: 本 §3 (eval mode protocol)、本 §7 (failure attribution methodology)、本 §8 (ablation study spec)、本 §9 (ground truth comparison protocol)、本 §11 (reproducibility checklist)
- **Eval mode protocol**: cuda:2 deterministic kernel + fixed global seed=42 + per-restart seed derivation `seed_per_restart = seed_base + restart_idx` + batch size B=1 (per-scene serial、N=120 sequential ≈ 120 × ~50ms = ~6s wall) + multi-restart serial fallback (vmap experimental、bit-identical 維持優先)
- **Ground truth comparison protocol**: newton env state dump (`env.scene["cable"].body_q[batch, segment_idx, 0:3]`) → 40-segment world-frame xyz → per-segment L2 distance vs estimator output。**注**: GT は env-side acquisition のみ、estimator core 内では `EstimatorLabelsForEvalOnly` boundary 経で smuggling 防止 (parent §6.3)
- **Q5 verdict**: 7 gates (random_mean<5mm + random_p95<10mm + ushape 10/10 + sshape 10/10 + identity_inversion=0 + ECE<5% + latency_p95<50ms) 全 PASS 経で `overall_passed=True`、1 gate FAIL → failure attribution per-stage diagnostics aggregator (§6) 経で primary cause 特定
- **Ablation study**: 4 axis × 3-5 cell × 5 seed = ~60-80 cell × ~5s/scene × 120 scenes ≈ ~10-16h GPU、minimum-viable subset (4 axis × 1 cell × 1 seed ≈ ~30 min GPU、Phase 7 必須) + full sweep optional (Phase 8 候補)
- **Reporting format**: per-scene CSV (downstream pandas) + Q5 verdict JSON (machine-readable) + summary md (human-readable) の 3-format multi-output、parquet alternative 対象外 (依存追加 cost > 価値)
- **Phase 番号 renumber 注**: Phase 3 で 1-shift 済 (旧 Phase 3=Stage C train → 新 Phase 4)、本 task が Phase 4 = Validation Design 占有 → 旧 Phase 4-6 を新 Phase 5-7 に shift (本 §1.4)

---

## §1 Scope + Phase renumber + per-section ownership

### §1.1 In-scope (本 Phase 4 design phase)

1. **Eval mode protocol** (§3): deterministic seed + cuda:2 kernel + multi-restart determinism + batch sizing
2. **Per-scene metric implementation** (§4): Q5SceneMetrics dataclass field + return type freeze + per-stage diagnostics consumption
3. **PASS criteria evaluator final** (§5): 7 gates + per-gate threshold rationale + tie-breaking + edge case handling
4. **Per-stage diagnostics aggregator final** (§6): 10 thresholds + threshold revision pathway + Q5StageDiagnosticsReport finalization
5. **Failure attribution methodology** (§7): per-scene F1-F12 mapping + primary/secondary cause classification + tie-breaking rule
6. **Ablation study spec** (§8): 4 axis × cell count + GPU budget + minimum-viable subset + Phase 5-6 impl ablation hooks
7. **Ground truth comparison protocol** (§9): newton state dump → 40-segment GT → metric pipeline + R6 boundary preservation
8. **Reporting format spec** (§10): CSV schema + JSON verdict schema + summary md template + downstream consumption
9. **Reproducibility checklist** (§11): 15+ items (commit + dataset + checkpoint + hyperparams + env + GPU + deps)
10. **Phase 7 trigger spec + spec source pointer** (§12)

### §1.2 Out-of-scope (Phase 5-7 別 NEST node)

- Phase 5 (`T-Vision-CableState-Impl-Phase-5-Stage-C-Train`、原 Phase 4 from Phase 3 renumber): Stage C DD-PINN train (~25h GPU + 5k labeled scenes generation infrastructure + checkpoint 生成)
- Phase 6 (`T-Vision-CableState-Impl-Phase-6-Stage-DE`、原 Phase 5): Stage D Cosserat 7-term loss impl (PyTorch L-BFGS gradient computation + multi-restart + identity inversion check) + Stage E ECE calibration (val 1k sample logistic regression coefficient fit) + `cable_state.py` `CableStateSolver` orchestrator delegate fill
- Phase 7 (`T-Vision-CableState-Impl-Phase-7-Q5-Bench`、原 Phase 6): Q5 worst-case benchmark execution (10 U + 10 S scripted scenes + N=100 random + ECE measurement + identity inversion 0% verify + latency p95 <50ms verify + ablation study run)
- Warp kernel optimization (latency-critical 化判断は Phase 7 latency profile 経で defer、別 leaf `T-Vision-CableState-Impl-Phase-8-Warp` 候補)
- 04-Specs SSOT update (Rs専権、Vault Write Permissions)
- env file / `cable_state*.py` impl-time 改変 (本 Phase 4 では reference のみ)

### §1.3 Phase 4 deliverable summary

| deliverable | path | LoC est. | status |
|-------------|------|----------|--------|
| state.md | `T-Vision-CableState-Impl-Phase-4-Validation-Design/state.md` | ~250 | (本 leaf) |
| design memo | `06-Knowledge/LL-Vision-CableState-Phase4-Validation-Design.md` (本 file) | ~800 | (本 leaf) |
| parent state update | `T-Vision-CableState/state.md` | +5 | (本 leaf) |
| manifest update | `00-Project-Management/project-tree-manifest.md` | +20 | (本 leaf) |
| Tier 2 deposit | `_edit_requests/NNNNN-T-Vision-CableState-Impl-Phase-4-Validation-Design-init.md` | ~200 | (本 leaf) |
| memory entry | `~/.claude/projects/.../memory/project_t_vision_cable_state_impl_phase4_validation_design_2026-05-04.md` | ~50 | (本 leaf) |

### §1.4 Phase 番号 renumber (Phase 3 precedent と同 pattern)

Phase 3 design memo (`LL-Vision-CableState-Phase3-Integration-Design.md` §1.4) で旧 Phase 3-5 → 新 Phase 4-6 に 1-shift 済。本 task が "Phase 4 = Validation Design" を占有、よって以降の renumber:

| Phase 3 後 (renumber 1) | 本 task 後 (renumber 2) | 内容 | LoC + GPU | 起票 trigger |
|--------------------------|-------------------------|------|-----------|--------------|
| Phase 1 (unchanged) | Phase 1 (unchanged) | Stage A.3 + B + camera infra (COMPLETE 2026-05-04T03:50) | ~580 LoC + 0 GPU | (済) |
| Phase 2 (unchanged) | Phase 2 (unchanged) | Stage C/D/E design + skeleton (COMPLETE 2026-05-04T03:55) | ~580 LoC + 0 GPU | (済) |
| Phase 3 (Integration Design) | Phase 3 (unchanged) | Stages A-E integration design + Q5 protocol initial (COMPLETE 2026-05-04T05:05) | ~600 行 doc + 0 GPU | (済) |
| (none) | **Phase 4 (NEW、本 leaf)** | **Validation methodology + benchmark protocol final** | **~700-900 行 doc + 0 GPU + ~1-2h wall** | (本 leaf 進行中) |
| Phase 4 (Stage C train) | Phase 5 (Stage C train) | Stage C DD-PINN train | ~180 LoC + ~25h GPU | 5k dataset ready + Rs §3.1 #4 |
| Phase 5 (Stage D/E impl) | Phase 6 (Stage D/E impl) | Stage D Cosserat impl + Stage E ECE calibration | ~200 LoC + ~7h GPU | Phase 5 PASS + 1k val held-out |
| Phase 6 (Q5 benchmark execution) | Phase 7 (Q5 benchmark execution) | Q5 worst-case benchmark execution | ~80 LoC + ~5h GPU | Phase 6 COMPLETE + 10U/10S scripted scene env-side ready |

**注 (Phase 5-7 起票 spec source の更新)**: Phase 3 design memo §8 で "Phase 4 = Stage C train" と命名されていた entry は、本 task 経で "Phase 5 = Stage C train" に shift 解釈。Phase 5 起票時 cite で Phase 3 design memo §8.1 (Stage C train trigger) + 本 design memo §1.4 (Phase 番号 renumber 注) を併記推奨。同様 Phase 3 §8.2 → Phase 6 trigger、Phase 3 §8.3 → Phase 7 trigger。

### §1.5 Per-section ownership matrix vs Phase 3 §5 (本 leaf 中核 differentiation)

| Phase 3 § | 本 §  | ownership | level diff |
|-----------|-------|-----------|------------|
| §5.1 (eval dataset construction、scene composition) | §2 | finalized impl + jitter spec + metadata schema | skeleton (table only) → impl (function body + frozen schema) |
| §5.2 (per-scene evaluation function) | §4 | impl-ready (return type freeze + downstream consumption) | function signature → field-by-field impl spec |
| §5.3 (PASS criteria evaluator) | §5 | 7 gates final (per-gate rationale + tie-breaking + edge case) | gates list → gate spec with edge cases |
| §5.4 (per-stage diagnostics aggregator) | §6 | 10 thresholds final (threshold revision pathway + report finalization) | thresholds + skeleton aggregator → impl aggregator + revision protocol |
| §5.5 (eval pipeline orchestration) | §10 | reporting format spec (CSV + JSON + md) | function spec → output format spec |
| (Phase 3 §5 で 不在) | §3 | NEW: eval mode protocol (deterministic + cuda:2 + batch + multi-restart) | (full new spec) |
| (Phase 3 §5 で 不在) | §7 | NEW: failure attribution methodology (F1-F12 → stage threshold mapping) | (full new spec) |
| (Phase 3 §5 で 不在) | §8 | NEW: ablation study spec (4 axis × cell × seed + GPU budget) | (full new spec) |
| (Phase 3 §5 で 不在) | §9 | NEW: ground truth comparison protocol (newton state dump + R6 boundary) | (full new spec) |
| (Phase 3 §5 で 不在) | §11 | NEW: reproducibility checklist (commit + dataset + checkpoint + ...) | (full new spec) |

---

## §2 Eval dataset finalization (Phase 3 §5.1 拡張)

### §2.1 Scene composition (Phase 3 §5.1.1 直引き freeze)

| dataset | count | source | scenario | seed |
|---------|-------|--------|----------|------|
| Random clip routing | 100 | held-out 5-clip routing snapshots | random Phase / skill / cable shape | seed=42 |
| U-shape worst-case | 10 | scripted env (cable folding) | mid-cable folds back, 2 modes、varied fold positions × 2 fold-depth | seed=43 |
| S-shape worst-case | 10 | scripted env (2 inflection points) | 3 modes、varied insertion depths × clip combinations | seed=44 |

**total**: 120 scenes。

### §2.2 Random scene specification finalized

```python
@dataclass(frozen=True)
class RandomSceneSamplingConfig:
    """Configuration for random scene sampling from held-out 5-clip routing dataset."""
    seed: int = 42
    n_scenes: int = 100

    # Phase variety distribution (parent §5.1.2 直引き)
    phase_distribution: dict[str, float] = field(default_factory=lambda: {
        "approach":  0.20,
        "grip":      0.10,
        "lift":      0.10,
        "transport": 0.20,
        "insert":    0.30,
        "release":   0.10,
    })

    # Cable shape variety distribution (parent §5.1.2 直引き)
    cable_shape_distribution: dict[str, float] = field(default_factory=lambda: {
        "straight": 0.50,
        "bent":     0.30,
        "complex":  0.20,
    })

    # Skill mid-execution states (no end-of-episode bias)
    sampling_episode_step_range: tuple[float, float] = (0.10, 0.90)  # 10-90% of episode
```

**実 sampling impl (Phase 7 reference)**:

```python
def sample_random_scenes(
    held_out_replay: HeldOutReplayLog,
    config: RandomSceneSamplingConfig,
) -> list[Q5SceneSpec]:
    """Sample N=100 random scenes from held-out 5-clip routing replay log."""
    rng = np.random.default_rng(config.seed)
    scenes = []
    target_phase_counts = {phase: int(config.n_scenes * frac)
                           for phase, frac in config.phase_distribution.items()}
    target_shape_counts = {shape: int(config.n_scenes * frac)
                           for shape, frac in config.cable_shape_distribution.items()}

    # Sample phase × shape grid (rejection-sampling for distribution match)
    for phase, n_phase in target_phase_counts.items():
        for shape, n_shape in target_shape_counts.items():
            n_cell = round(n_phase * (n_shape / config.n_scenes))
            candidates = held_out_replay.filter(
                phase=phase, cable_shape=shape,
                episode_step_pct_range=config.sampling_episode_step_range,
            )
            sampled = rng.choice(candidates, size=n_cell, replace=False)
            scenes.extend(sampled)

    # Truncate / pad to exactly n_scenes if rounding mismatch
    scenes = scenes[:config.n_scenes]
    return [_freeze_scene(s, scene_id=f"random_{i:03d}") for i, s in enumerate(scenes)]
```

### §2.3 U-shape scripted scenario detail (Phase 3 §5.1.3 直引き + jitter spec)

```
Step 1: Cable initially routed through clip[0], clip[1], clip[2] (Phase 5-3 baseline state)
Step 2: Robot grasps cable at mid-segment seg[k], k ∈ {15, 18, 20, 22, 25}
Step 3: Robot pulls grasp_pos toward back (z+0.05m to z+0.10m, y-0.10m world)
Step 4: Snapshot at fold-active frame (cable folded ~180°)
Expected: PCA var_ratio ≈ 0.4-0.5
```

**Per-scene jitter spec (本 leaf 新規)**:

```python
@dataclass(frozen=True)
class UShapeSceneSpec:
    fold_segment_idx: int          # k ∈ {15, 18, 20, 22, 25}
    fold_depth: str                # "medium" (z+0.05m) | "deep" (z+0.10m)
    seed: int                      # per-scene jitter seed (43 + idx)

    # Per-scene jitter (本 leaf 新規 spec、reproducibility 用):
    cable_initial_perturbation_std: float = 0.005  # 5mm cable layout noise
    grasp_position_perturbation_std: float = 0.003  # 3mm grasp position noise
    fold_orientation_jitter_rad: float = 0.05       # ±2.9° fold rotation noise
```

10 scene generation matrix: 5 fold positions × 2 fold-depths = 10 scenes (seed=43 + per-scene jitter `seed_i = 43 + i for i in 0..9`)。

### §2.4 S-shape scripted scenario detail (Phase 3 §5.1.4 直引き + jitter spec)

```
Step 1: Cable initially routed through clip[0], clip[1], clip[2], clip[3], clip[4]
Step 2: Insert cable into clip[m] groove (1st inflection)
Step 3: Insert cable into clip[n] groove (2nd inflection)
Step 4: Snapshot at inserted state (S-curve formed)
Expected: PCA var_ratio ≈ 0.3-0.4
```

**Per-scene jitter spec (本 leaf 新規)**:

```python
@dataclass(frozen=True)
class SShapeSceneSpec:
    inflection_clip_pair: tuple[int, int]  # (m, n) ∈ {(0, 2), (0, 3), (1, 3), (2, 4), (1, 4)}
    insertion_depth: str                   # "shallow" (5mm into groove) | "deep" (12mm into groove)
    seed: int                              # per-scene jitter seed (44 + idx)

    # Per-scene jitter (本 leaf 新規 spec):
    cable_initial_perturbation_std: float = 0.005
    insertion_position_jitter_std: float = 0.003
    inflection_orientation_jitter_rad: float = 0.05
```

10 scene generation matrix: 5 inflection clip pairs × 2 insertion depths = 10 scenes (seed=44 + per-scene jitter `seed_i = 44 + i for i in 0..9`)。

### §2.5 Q5SceneSpec finalization (Phase 3 §5.1.2 拡張 metadata schema)

```python
@dataclass(frozen=True)
class Q5SceneSpec:
    """Single scene metadata + inputs + ground truth for Q5 benchmark.

    Phase 4 final freeze: 本 dataclass の field schema は Phase 7 まで UNCHANGED、
    新 field 追加は Phase 4-revision レベル task で起票。
    """
    # Identification
    scene_id: str                              # "random_001", "ushape_005", "sshape_003" 等
    scene_type: str                            # "random" | "ushape" | "sshape"
    seed: int                                  # per-scene jitter seed
    sampling_seed: int                         # parent sampling seed (42 / 43 / 44)

    # Inputs
    inputs: "EstimatorInputs"                   # rgb / depth / cam_poses / intrinsics / finger_positions / prev (None for episode start)
                                                # 注: types.py freeze、本 leaf で field 追加なし

    # Ground truth (env-side acquired、estimator core 内で直接 access 禁止 per parent §6.3)
    ground_truth: torch.Tensor                  # [40, 3] world-frame xyz [m]、newton env state dump 経 (§9 参照)
    ground_truth_acquisition_method: str       # "newton_body_q_dump" (本 phase の唯一 method)

    # Metadata for analysis & failure attribution
    scene_metadata: dict[str, Any] = field(default_factory=dict)
    # expected fields:
    #   "phase":       str (random scene の phase: "approach" | ... | "release")
    #   "cable_shape": str (random scene: "straight" | "bent" | "complex"; worst-case: "U" | "S")
    #   "episode_id":  str (random scene の元 episode reference)
    #   "episode_step_pct": float (random scene の episode position)
    #   "fold_segment_idx" / "fold_depth": int / str (U-shape のみ)
    #   "inflection_clip_pair" / "insertion_depth": tuple / str (S-shape のみ)
    #   "expected_var_ratio_range": tuple[float, float] (worst-case のみ、§2.3+§2.4 spec 経)

    # Reproducibility hash (本 leaf 新規)
    inputs_sha256: str                          # hash of inputs tensors (R6 boundary obs only)
    ground_truth_sha256: str                    # hash of ground truth tensor
```

**Frozen schema enforcement (Phase 7 起票時 spec source)**:
- Phase 7 で `tests/test_q5_scene_spec_schema.py` 新規 test 起票候補 (本 dataclass の field 列挙が本 leaf §2.5 と一致 assert)
- field 追加は Phase 4-revision レベル task で起票 (本 leaf 完走後の revision)

---

## §3 Eval mode protocol (本 leaf 新規)

### §3.1 Determinism spec

| component | determinism technique | rationale |
|-----------|----------------------|-----------|
| Global Python random | `random.seed(42)` | numpy / scripts random call coverage |
| NumPy | `np.random.default_rng(42)` (per-scope rng instance、global state 汚染回避) | reproducibility + per-restart seed derivation |
| PyTorch CPU | `torch.manual_seed(42)` | model init + dropout + sampling layer (DD-PINN 内 dropout なし、安全) |
| PyTorch CUDA | `torch.cuda.manual_seed(42)` + `torch.backends.cudnn.deterministic = True` + `torch.backends.cudnn.benchmark = False` | cuda:2 deterministic kernel (parent §1.1 + CC4 v3.2 §10) |
| PyTorch L-BFGS line search | (内部 line search に non-determinism 余地、Phase 7 で empirical bit-identical check) | gradient computation deterministic、line search step は seed-based ε-perturbation |
| Multi-restart | per-restart seed = `seed_base + restart_idx` (§3.2 詳細) | restart 毎 reproducibility + parallel-friendly |
| FPS sampling (Stage C anchor) | per-scene seed-based farthest point sampling (initial seed point = `rng.integers(N_pts)`) | reproducibility |

### §3.2 Per-restart seed derivation

```python
def derive_restart_seed(scene_seed: int, restart_idx: int) -> int:
    """Derive per-restart seed from scene seed.

    Goal: 各 restart deterministic、5-restart Phase 7 で identical perturbation noise reproducibility。
    """
    return scene_seed * 1000 + restart_idx  # 一意性 (scene_seed up to 999、restart_idx up to 4)

# Phase 6 (Stage D Cosserat impl) で使用 reference:
def cosserat_multi_restart_fit(seg_init, cloud, prev, finger, scene_seed):
    best_loss = float("inf")
    best_seg = seg_init
    for restart_idx in range(5):
        restart_seed = derive_restart_seed(scene_seed, restart_idx)
        torch.manual_seed(restart_seed)
        perturbation = torch.randn_like(seg_init) * 0.002  # σ=2mm
        seg_perturbed = seg_init + perturbation
        seg_fitted, loss = run_lbfgs(seg_perturbed, cloud, prev, finger)
        if loss < best_loss:
            best_loss = loss
            best_seg = seg_fitted
    return best_seg, {"restart_used": int(np.argmin([loss_history]))}
```

### §3.3 Batch sizing

- **B=1 (per-scene serial)**: N=120 sequential ≈ 120 × ~50ms = ~6s wall (latency budget per Phase 3 §6.1)
- **rationale for B=1**: (a) Phase 3 §3.3 `CableStateSolver.__call__` は per-scene single instance call、batch dim は L-BFGS 内部 implicit、(b) ablation study (§8) で multi-restart parallelization 検討、本 phase では eval simplicity 優先
- **alternative (Phase 7 で revision candidate)**: B>1 vmap で multi-scene batched (但し L-BFGS state batching は PyTorch 2.0 vmap で experimental)、cuda:2 GPU 帯域使用率向上

### §3.4 Multi-restart determinism (本 §3.2 詳細補足)

Phase 6 Stage D Cosserat impl で 5-restart × σ=2mm spec (Phase 2 design memo §3.5 既存)、本 §3.2 で per-restart seed derivation 経で各 restart deterministic。Phase 7 で empirical bit-identical reproducibility check:

```python
# Phase 7 reference test pattern:
def test_q5_bit_identical_5_run():
    """Q5 verdict が 5 run で identical reproducibility (本 §3.1+§3.2 spec 経)."""
    verdicts = []
    for _ in range(5):
        verdict, _ = run_q5_benchmark(pipeline, estimator, eval_dataset, output_dir=tmpdir)
        verdicts.append(verdict.overall_passed)
    assert all(v == verdicts[0] for v in verdicts), "verdict mismatch across 5 runs"

    # Threshold-based: metric within ε=1e-6 (line search ε-perturbation 経の minor difference 許容)
    metrics = [v.random_mean_error_m for v in verdicts]
    assert max(metrics) - min(metrics) < 1e-6, "metric drift across runs"
```

### §3.5 cuda:2 vs CPU determinism trade-off

- **cuda:2 deterministic kernel** (CC4 v3.2 §10 + parent §1.1 既存 spec): GPU 高速 + reproducibility 確保 (cudnn deterministic mode)
- **CPU fallback**: GPU memory pressure (>20GB)、debug 用 deterministic mode (CPU は GPU と若干違 metric possible due to floating-point order)、本 phase は cuda:2 default、CPU は backup
- **GPU vs CPU bit-identical**: 不保証 (cudnn deterministic mode は同 GPU 内のみ、CPU は別 path)。Phase 7 では cuda:2 verdict が canonical、CPU verdict は debug only

### §3.6 Eval-time invariants (本 §3 spec の Phase 7 enforcement)

Phase 7 起票時、eval pipeline 開始直前に以下 invariants check:

```python
def assert_eval_mode_invariants():
    """本 §3 spec の Phase 7 enforcement (eval pipeline 開始直前 assert)."""
    assert torch.backends.cudnn.deterministic, "cudnn deterministic mode required"
    assert not torch.backends.cudnn.benchmark, "cudnn benchmark mode disabled"
    assert torch.cuda.is_available(), "cuda required for canonical eval"
    cuda_device_idx = torch.cuda.current_device()
    assert cuda_device_idx == 2 or os.environ.get("CUDA_VISIBLE_DEVICES") in ("2", "0"), \
        "cuda:2 (or CUDA_VISIBLE_DEVICES=2 + cuda:0 within visibility) required"
    # Phase 5 train + Phase 6 impl 由来 checkpoint hash を verdict に embed (§11 reproducibility)
```

---

## §4 Per-scene metric implementation (Phase 3 §5.2 拡張)

### §4.1 Q5SceneMetrics finalization

```python
@dataclass
class Q5SceneMetrics:
    """Single scene evaluation result (Phase 4 finalized field schema、Phase 7 まで UNCHANGED)."""
    # Identification (Q5SceneSpec から pass-through)
    scene_id: str
    scene_type: str

    # Primary error metrics
    mean_error_m: float                # ē = mean per-segment error [m]
    p95_error_m: float                  # 95th percentile per-segment error [m]
    max_error_m: float                  # max per-segment error [m]

    # Per-segment detail (for global ECE + ablation study)
    per_seg_errors: torch.Tensor        # [40] L2 distance per-segment [m]
    per_seg_confidences: torch.Tensor   # [40] confidence per-segment ∈ [0, 1]

    # Topology
    identity_inversion: bool            # check_inversion(P̂_seg, GT、threshold 0.05m per Phase 3 §5.2)
    has_nan_segments: bool              # any NaN in P̂_seg (count: nan_segment_count for diagnostics)
    nan_segment_count: int              # # of NaN segments in P̂_seg (0..40)

    # Latency
    total_latency_ms: float             # CableStateSolver.__call__ end-to-end ms
    stage_a_b_latency_ms: float         # Phase 1 (MultiCamCableStatePipeline.estimate_with_cloud) ms

    # Per-stage diagnostics (Phase 3 §3.4 schema 直引き、本 phase で freeze)
    stage_diagnostics: dict             # Phase 3 §3.4 schema:
                                        # {stage_a3, stage_b, stage_c_triggered, stage_c, stage_d, identity_inversion_detected, stage_e, total_latency_ms}

    # Reproducibility metadata (本 leaf 新規)
    eval_run_metadata: "EvalRunMetadata"  # commit_sha, dataset_sha, checkpoint_sha, etc. (§11)

def evaluate_scene(
    estimator: "CableStateSolver",
    pipeline: "MultiCamCableStatePipeline",
    scene: Q5SceneSpec,
    eval_run_metadata: "EvalRunMetadata",
) -> Q5SceneMetrics:
    """Phase 7 impl reference pattern."""
    # 1. Run pipeline.estimate_with_cloud (Phase 3 §2.2 adapter spec 経)
    t_pipeline_start = time.perf_counter()
    phase1_result, cloud = pipeline.estimate_with_cloud(
        finger_positions=scene.inputs.finger_positions,
        prev=None,  # Phase 7 では per-scene independent (no prev frame、worst-case 単発 evaluation)
    )
    stage_a_b_latency_ms = (time.perf_counter() - t_pipeline_start) * 1000.0

    # 2. Run estimator (Phase 3 §3.3 spec 経)
    cable_state = estimator(
        cloud=cloud,
        phase1_result=phase1_result,
        prev=None,
        finger_positions=scene.inputs.finger_positions,
    )

    # 3. Compute per-segment errors
    per_seg_errors = torch.norm(cable_state.positions - scene.ground_truth, dim=-1)  # [40]
    per_seg_errors_clean = per_seg_errors[~torch.isnan(per_seg_errors)]  # NaN seg は exclude for stats

    mean_error = per_seg_errors_clean.mean().item() if len(per_seg_errors_clean) > 0 else float("nan")
    p95_error = torch.quantile(per_seg_errors_clean, 0.95).item() if len(per_seg_errors_clean) > 0 else float("nan")
    max_error = per_seg_errors_clean.max().item() if len(per_seg_errors_clean) > 0 else float("nan")

    # 4. Identity inversion check (Phase 3 §5.2 spec 経)
    identity_inversion = check_identity_inversion(cable_state.positions, scene.ground_truth, threshold_m=0.05)

    # 5. NaN segment count
    nan_mask = torch.isnan(cable_state.positions).any(dim=-1)  # [40] bool
    has_nan = nan_mask.any().item()
    nan_count = nan_mask.sum().item()

    return Q5SceneMetrics(
        scene_id=scene.scene_id,
        scene_type=scene.scene_type,
        mean_error_m=mean_error,
        p95_error_m=p95_error,
        max_error_m=max_error,
        per_seg_errors=per_seg_errors,
        per_seg_confidences=cable_state.confidences,
        identity_inversion=identity_inversion,
        has_nan_segments=has_nan,
        nan_segment_count=nan_count,
        total_latency_ms=stage_a_b_latency_ms + cable_state.stage_diagnostics["total_latency_ms"],
        stage_a_b_latency_ms=stage_a_b_latency_ms,
        stage_diagnostics=cable_state.stage_diagnostics,
        eval_run_metadata=eval_run_metadata,
    )
```

### §4.2 Identity inversion check final

```python
def check_identity_inversion(
    seg_estimated: torch.Tensor,        # [40, 3]
    seg_gt: torch.Tensor,                # [40, 3]
    threshold_m: float = 0.05,
) -> bool:
    """Identity inversion: P̂_seg(0) maps to GT seg(39) or vice versa.

    Algorithm (Phase 3 §5.2 spec 経):
      - Compute aligned dist: ‖P̂_seg - seg_gt‖₂.mean()
      - Compute reversed dist: ‖P̂_seg - flip(seg_gt)‖₂.mean()
      - if (reversed_dist + threshold_m) < aligned_dist:
          # Reversed direction is significantly closer → inversion suspected
          return True
      - else:
          return False
    """
    # Filter out NaN segments for fair comparison
    nan_mask = torch.isnan(seg_estimated).any(dim=-1) | torch.isnan(seg_gt).any(dim=-1)
    valid_mask = ~nan_mask

    if valid_mask.sum() < 5:  # < 5 valid segments、判定不可、conservative → False (no inversion)
        return False

    seg_est_valid = seg_estimated[valid_mask]
    seg_gt_valid = seg_gt[valid_mask]
    seg_gt_reversed = torch.flip(seg_gt_valid, dims=[0])  # 反転 valid segments

    aligned_dist = torch.norm(seg_est_valid - seg_gt_valid, dim=-1).mean()
    reversed_dist = torch.norm(seg_est_valid - seg_gt_reversed, dim=-1).mean()

    return bool((reversed_dist + threshold_m) < aligned_dist)
```

**Edge case handling**:
- 全 segments NaN (cable mask 全失敗): `valid_mask.sum() == 0` → False (no inversion judged、Stage A FAIL_CLOSED で別途 captureされる)
- 一部 segments NaN: valid mask で filtering、5 segments minimum で判定可能性確保

### §4.3 NaN handling in metric computation

| condition | action | rationale |
|-----------|--------|-----------|
| Estimator P̂_seg に NaN 含む | exclude from per_seg_errors stats、has_nan_segments=True、nan_segment_count 記録 | 連続 NaN は Stage A FAIL_CLOSED 経の fallback indicator (Phase 3 §2.3) |
| Ground truth に NaN 含む | env state dump 不正 (本 phase では起こらないはず)、Phase 7 で assert | data integrity check |
| 全 estimator NaN (Phase 1 全 fail): P̂_seg = prev (or zeros) | fallback case、stage_diagnostics["fallback"] field で識別 (Phase 3 §3.4 既存 schema) | Stage A FAIL_CLOSED 経 |
| identity_inversion check 不能 (valid<5 segs) | False (no inversion judged) | conservative、Stage A FAIL_CLOSED で別 path |

---

## §5 PASS criteria evaluator final (Phase 3 §5.3 拡張)

### §5.1 7 gates final spec (Phase 3 §5.3 直引き + per-gate rationale + edge case)

| gate name | metric | threshold | rationale | edge case handling |
|-----------|--------|-----------|-----------|---------------------|
| `random_mean_error_lt_5mm` | mean over 100 random scenes of `mean_error_m` | < 0.005 m | parent §1.1 + EXP-046 single-midpoint 3.92mm baseline 経 | NaN scenes は除外して mean 計算、NaN scene 数 ≥ 10 → Gate FAIL (data integrity) |
| `random_p95_error_lt_10mm` | mean over 100 random scenes of `p95_error_m` | < 0.010 m | tail handling: worst seg of typical scene、parent §1.1 直引き | 同上 |
| `ushape_all_lt_5mm` | all 10 ushape scenes の `mean_error_m` < 0.005 m | individual scene compliance | parent §1.1 + worst-case mitigation requirement (CC8 KA2 ACCEPT) | 1 scene NaN → Gate FAIL (10/10 全件 compliance 必須) |
| `sshape_all_lt_5mm` | all 10 sshape scenes の `mean_error_m` < 0.005 m | individual scene compliance | parent §1.1 + worst-case mitigation requirement | 同上 |
| `zero_identity_inversion` | sum over 120 scenes of `identity_inversion` | == 0 | wrong identity = task failure (parent §3.1 cascade fail) | identity_inversion check 不能 scene は除外、count ≤ 5 まで許容、6+ → Gate FAIL (data integrity) |
| `ece_lt_5pct` | global ECE over 120 scenes | < 0.05 | parent §2.6.2 + Phase 3 §5.3 既存 | per-bin sample count < 10 bin は除外、≥ 5 bin 残れば計算 |
| `latency_p95_lt_50ms` | p95 over 120 scenes of `total_latency_ms` | < 50.0 ms | parent §2.5.3 + Phase 3 §6.1 latency budget | timeout scene (latency > 1000ms) は exclusionせず p95 計算 (worst-case capture) |

**Gate decision rule**: 7 gates 全 PASS で `overall_passed=True`。1 gate でも FAIL → Q5 gate FAIL、failure attribution per-stage diagnostics aggregator (§6) 経で primary cause 特定 (§7)。

### §5.2 Q5BenchVerdict finalization

```python
@dataclass
class Q5BenchVerdict:
    """Q5 gate PASS / FAIL verdict (Phase 4 finalized schema、Phase 7 まで UNCHANGED)."""
    # Overall verdict
    overall_passed: bool
    per_gate_status: dict[str, bool]    # gate_name → passed (本 §5.1 7 gates)

    # Per-gate detailed metrics
    random_mean_error_m: float          # mean over 100 random scenes
    random_p95_error_m: float           # mean over 100 random p95
    ushape_mean_errors_m: list[float]   # per-scene means [10]
    sshape_mean_errors_m: list[float]   # per-scene means [10]
    identity_inversion_count: int       # /120 total
    overall_ece: float
    latency_p95_ms: float

    # Failure attribution (§7 spec、本 leaf 新規)
    primary_failure_cause: str | None   # F1-F12 の primary mode (None if PASS)
    secondary_failure_causes: list[str] # F1-F12 の secondary modes (empty if PASS)

    # Reproducibility metadata (§11)
    metadata: "EvalRunMetadata"          # commit_sha + dataset_sha + checkpoint_sha + ...

    # Per-scene aggregates
    n_random_scenes: int                # = 100 expected
    n_ushape_scenes: int                # = 10 expected
    n_sshape_scenes: int                # = 10 expected
    n_excluded_scenes: int              # NaN-only scenes excluded (data integrity check)

    def to_summary_md(self) -> str:
        """Human-readable summary (§10.4 spec 経)."""
        ...
```

### §5.3 evaluate_q5_gate impl-ready spec

```python
def evaluate_q5_gate(per_scene_metrics: list[Q5SceneMetrics], metadata: "EvalRunMetadata") -> Q5BenchVerdict:
    """Aggregate per-scene metrics into Q5 gate verdict (Phase 7 impl reference)."""
    random_metrics = [m for m in per_scene_metrics if m.scene_type == "random"]
    ushape_metrics = [m for m in per_scene_metrics if m.scene_type == "ushape"]
    sshape_metrics = [m for m in per_scene_metrics if m.scene_type == "sshape"]

    # Data integrity check
    n_excluded = sum(1 for m in per_scene_metrics if math.isnan(m.mean_error_m))
    n_random_excluded = sum(1 for m in random_metrics if math.isnan(m.mean_error_m))
    if n_random_excluded >= 10:
        return _verdict_data_integrity_fail(metadata, n_excluded, "random scenes NaN ≥ 10")

    # Filter NaN scenes per gate type
    random_clean = [m for m in random_metrics if not math.isnan(m.mean_error_m)]

    gates = {}

    # Gate 1+2: Random scenes
    random_mean_error = sum(m.mean_error_m for m in random_clean) / len(random_clean)
    random_p95_error = sum(m.p95_error_m for m in random_clean) / len(random_clean)
    gates["random_mean_error_lt_5mm"] = random_mean_error < 0.005
    gates["random_p95_error_lt_10mm"] = random_p95_error < 0.010

    # Gate 3: U-shape (10/10 strict compliance)
    gates["ushape_all_lt_5mm"] = (
        len(ushape_metrics) == 10
        and all(m.mean_error_m < 0.005 for m in ushape_metrics if not math.isnan(m.mean_error_m))
        and not any(math.isnan(m.mean_error_m) for m in ushape_metrics)
    )

    # Gate 4: S-shape (10/10 strict compliance)
    gates["sshape_all_lt_5mm"] = (
        len(sshape_metrics) == 10
        and all(m.mean_error_m < 0.005 for m in sshape_metrics if not math.isnan(m.mean_error_m))
        and not any(math.isnan(m.mean_error_m) for m in sshape_metrics)
    )

    # Gate 5: Identity inversion (0% target)
    inversion_count = sum(int(m.identity_inversion) for m in per_scene_metrics)
    gates["zero_identity_inversion"] = inversion_count == 0

    # Gate 6: ECE
    overall_ece = compute_global_ece(per_scene_metrics)
    gates["ece_lt_5pct"] = overall_ece < 0.05

    # Gate 7: Latency p95
    all_latencies = sorted(m.total_latency_ms for m in per_scene_metrics)
    p95_idx = int(0.95 * len(all_latencies))
    latency_p95 = all_latencies[p95_idx]
    gates["latency_p95_lt_50ms"] = latency_p95 < 50.0

    overall_passed = all(gates.values())

    # Failure attribution (§7 spec)
    primary_cause, secondary_causes = (
        attribute_failure(per_scene_metrics, gates)
        if not overall_passed
        else (None, [])
    )

    return Q5BenchVerdict(
        overall_passed=overall_passed,
        per_gate_status=gates,
        random_mean_error_m=random_mean_error,
        random_p95_error_m=random_p95_error,
        ushape_mean_errors_m=[m.mean_error_m for m in ushape_metrics],
        sshape_mean_errors_m=[m.mean_error_m for m in sshape_metrics],
        identity_inversion_count=inversion_count,
        overall_ece=overall_ece,
        latency_p95_ms=latency_p95,
        primary_failure_cause=primary_cause,
        secondary_failure_causes=secondary_causes,
        metadata=metadata,
        n_random_scenes=len(random_metrics),
        n_ushape_scenes=len(ushape_metrics),
        n_sshape_scenes=len(sshape_metrics),
        n_excluded_scenes=n_excluded,
    )
```

### §5.4 ECE computation (本 §5 補足、Phase 3 §5.3 Gate 6)

```python
def compute_global_ece(
    per_scene_metrics: list[Q5SceneMetrics],
    n_bins: int = 10,
    error_threshold_correct: float = 0.005,  # 5mm = "correct" prediction
) -> float:
    """Global ECE (Expected Calibration Error) over all per-segment confidences.

    Algorithm (本 §5 補足):
      1. Flatten per-segment errors + confidences across all scenes
      2. Bin by confidence (10 equal-width bins in [0, 1])
      3. Per bin compute:
         - bin_mean_conf = mean(confidences in bin)
         - bin_acc = fraction of seg with error < error_threshold_correct
      4. ECE = Σ_bin (bin_count / total) × |bin_mean_conf - bin_acc|

    Edge case: bins with < 10 samples are skipped, ECE computed over remaining bins.
    """
    all_errors = torch.cat([m.per_seg_errors[~torch.isnan(m.per_seg_errors)] for m in per_scene_metrics])
    all_confs = torch.cat([m.per_seg_confidences[~torch.isnan(m.per_seg_errors)] for m in per_scene_metrics])

    if len(all_errors) == 0:
        return float("nan")

    bin_edges = torch.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    total = 0
    for i in range(n_bins):
        mask = (all_confs >= bin_edges[i]) & (all_confs < bin_edges[i + 1])
        if i == n_bins - 1:
            mask |= (all_confs == 1.0)  # right edge inclusion
        if mask.sum() < 10:
            continue
        bin_mean_conf = all_confs[mask].mean().item()
        bin_acc = (all_errors[mask] < error_threshold_correct).float().mean().item()
        bin_count = mask.sum().item()
        ece += bin_count * abs(bin_mean_conf - bin_acc)
        total += bin_count

    return ece / total if total > 0 else float("nan")
```

---

## §6 Per-stage diagnostics aggregator final (Phase 3 §5.4 拡張)

### §6.1 PER_STAGE_THRESHOLDS final (Phase 3 §5.4 直引き + revision pathway)

```python
PER_STAGE_THRESHOLDS = {
    # parent §5.4 + Phase 3 §5.4 直引き
    "A_n_pts":              {"warn": 1500,   "fail": 800,    "direction": "below", "unit": "count"},
    "A_per_cam_iou":        {"warn": 0.85,   "fail": 0.70,   "direction": "below", "unit": "ratio"},  # MVP-0B v2 ready 後
    "B_var_ratio_random":   {"warn": 0.7,    "fail": 0.6,    "direction": "below", "unit": "ratio"},  # random scene のみ
    "B_bin_emptiness":      {"warn": 4,      "fail": 8,      "direction": "above", "unit": "count"},
    "C_warm_mse":           {"warn": 0.008,  "fail": 0.015,  "direction": "above", "unit": "m"},
    "C_latency":            {"warn": 0.003,  "fail": 0.005,  "direction": "above", "unit": "s"},
    "D_residual":           {"warn": 0.002,  "fail": 0.005,  "direction": "above", "unit": "m"},  # = sqrt(L_pos / 40)
    "D_iter_count":         {"warn": 150,    "fail": 200,    "direction": "above", "unit": "count"},
    "E_ece":                {"warn": 0.05,   "fail": 0.10,   "direction": "above", "unit": "ratio"},  # global ECE
    "Total_latency":        {"warn": 0.05,   "fail": 0.10,   "direction": "above", "unit": "s"},  # = 50ms / 100ms
}
```

### §6.2 Threshold revision pathway

Phase 7 で empirical observation 経で revision candidate (Phase 3 §10 OQ-P3-2 + Phase 4 §8 OQ-P4-3 + 本 leaf §8 OQ-P4-3 既存 issue):

| trigger | revision direction | rationale |
|---------|---------------------|-----------|
| Phase 7 で random 80% 以上 が `B_var_ratio_random` warn (0.6-0.7 range) | warn 0.7 → 0.65 緩和、fail 0.6 維持 | empirical distribution に合わせ false-warn 削減 |
| Phase 7 で D_residual fail 高頻度 (>30% scenes) | warn 0.002 → 0.003 緩和 | empirical 0.005 fail strict だが 0.002 warn は too strict (Cosserat 残差は固有 noise floor あり) |
| Phase 7 で C_latency fail 高頻度 (>20% scenes) | warn 0.003 → 0.005、fail 0.005 → 0.008 緩和 | DD-PINN inference latency は cuda:2 device load 経で variability あり、初期 spec strict 過ぎ candidate |
| Phase 7 で `Total_latency` PASS (<50ms) でも per-stage warn 多数 | warn を per-stage 内訳で再 distribute | overall PASS でも per-stage breakdown で hidden bottleneck 検出 |

### §6.3 Q5StageDiagnosticsReport finalization

```python
@dataclass
class Q5StageDiagnosticsReport:
    """Per-stage failure attribution report (Phase 4 finalized、Phase 7 まで UNCHANGED)."""
    stage: str                            # "A" | "B" | "C" | "D" | "E" | "Identity" | "Total"
    metric_name: str                      # PER_STAGE_THRESHOLDS の key
    threshold_warn: float
    threshold_fail: float
    direction: str                         # "above" | "below"
    unit: str

    # Per-scene breakdown
    n_total_scenes: int                   # 評価対象 scene 数 (全 120 expected)
    n_warn_scenes: int                    # warn range scenes
    n_fail_scenes: int                    # fail range scenes
    n_pass_scenes: int                    # pass range scenes (n_total - n_warn - n_fail)

    # Examples for manual review
    fail_scene_ids: list[str]              # scenes that crossed fail threshold (top 10 by metric value)
    warn_scene_ids: list[str]              # scenes in warn range (top 10)

    # Statistics
    metric_min: float
    metric_max: float
    metric_mean: float
    metric_p95: float
    metric_p99: float

def aggregate_stage_diagnostics(per_scene_metrics: list[Q5SceneMetrics]) -> list[Q5StageDiagnosticsReport]:
    """Phase 7 impl reference."""
    reports = []
    for metric_key, thresh_spec in PER_STAGE_THRESHOLDS.items():
        # Extract per-scene metric value (per-stage diagnostics dict navigation)
        values = []
        scene_ids = []
        for m in per_scene_metrics:
            value = _extract_metric_from_diagnostics(m.stage_diagnostics, metric_key)
            if value is not None and not math.isnan(value):
                values.append(value)
                scene_ids.append(m.scene_id)

        if not values:
            continue

        # Classify per scene
        warn_indices = []
        fail_indices = []
        for i, v in enumerate(values):
            if thresh_spec["direction"] == "above":
                if v >= thresh_spec["fail"]:
                    fail_indices.append(i)
                elif v >= thresh_spec["warn"]:
                    warn_indices.append(i)
            else:  # below
                if v <= thresh_spec["fail"]:
                    fail_indices.append(i)
                elif v <= thresh_spec["warn"]:
                    warn_indices.append(i)

        # Top-10 fail scenes by metric distance from threshold
        fail_sorted = sorted(fail_indices, key=lambda i: abs(values[i] - thresh_spec["fail"]), reverse=True)
        warn_sorted = sorted(warn_indices, key=lambda i: abs(values[i] - thresh_spec["warn"]), reverse=True)

        values_t = torch.tensor(values)
        reports.append(Q5StageDiagnosticsReport(
            stage=metric_key.split("_")[0],
            metric_name=metric_key,
            threshold_warn=thresh_spec["warn"],
            threshold_fail=thresh_spec["fail"],
            direction=thresh_spec["direction"],
            unit=thresh_spec["unit"],
            n_total_scenes=len(values),
            n_warn_scenes=len(warn_indices),
            n_fail_scenes=len(fail_indices),
            n_pass_scenes=len(values) - len(warn_indices) - len(fail_indices),
            fail_scene_ids=[scene_ids[i] for i in fail_sorted[:10]],
            warn_scene_ids=[scene_ids[i] for i in warn_sorted[:10]],
            metric_min=values_t.min().item(),
            metric_max=values_t.max().item(),
            metric_mean=values_t.mean().item(),
            metric_p95=torch.quantile(values_t, 0.95).item(),
            metric_p99=torch.quantile(values_t, 0.99).item(),
        ))
    return reports
```

### §6.4 Diagnostics dict navigation (`_extract_metric_from_diagnostics`)

```python
def _extract_metric_from_diagnostics(diag: dict, metric_key: str) -> float | None:
    """Extract metric value from Phase 3 §3.4 stage_diagnostics schema."""
    mapping = {
        "A_n_pts":            ("stage_a3", "n_pts"),
        "A_per_cam_iou":      ("stage_a3", "per_cam_iou"),  # Phase 5+ で MVP-0B v2 ready 経 expose
        "B_var_ratio_random": ("stage_b", "var_ratio"),
        "B_bin_emptiness":    ("stage_b", "bin_emptiness_count"),  # Phase 5 で expose: sum(c == 0 for c in bin_counts)
        "C_warm_mse":         ("stage_c", "warm_mse"),  # Phase 5 で expose (vs GT)
        "C_latency":          ("stage_c", "latency_ms"),  # convert to seconds
        "D_residual":         ("stage_d", "final_loss"),  # = sqrt(L_pos / 40) approx
        "D_iter_count":       ("stage_d", "iter_count"),
        "E_ece":              ("stage_e", "ece_estimate"),  # Phase 5 で expose
        "Total_latency":      (None, "total_latency_ms"),  # convert to seconds
    }

    if metric_key not in mapping:
        return None

    section_key, field_key = mapping[metric_key]
    if section_key is None:
        value = diag.get(field_key)
    else:
        section = diag.get(section_key)
        if section is None:
            return None
        value = section.get(field_key) if isinstance(section, dict) else None

    if value is None:
        return None

    # Latency values: convert ms → seconds for thresh comparison
    if metric_key in ("C_latency", "Total_latency"):
        value = value / 1000.0

    return float(value)
```

---

## §7 Failure attribution methodology (本 leaf 新規)

### §7.1 F1-F12 → stage threshold mapping (Phase 3 §7 直引き + 本 leaf 拡張)

| F | mode (Phase 3 §7 直引き) | primary stage threshold (本 leaf 新規 mapping) | secondary stage threshold |
|---|--------------------------|------------------------------------------------|---------------------------|
| F1 | HSV mask drift (lighting / texture) | `A_per_cam_iou` < 0.70 (Phase 5+ MVP-0B v2 ready 後) | `A_n_pts` < 800 |
| F2 | Depth dropout (specular surface) | `A_n_pts` < 800 | `B_var_ratio_random` < 0.6 (sparse cloud → degenerate PCA) |
| F3 | Self-occlusion (cable under cable) | `B_bin_emptiness` > 8 | `D_residual` > 0.005 |
| F4 | PCA fail (U/S shape) | `B_var_ratio_random` < 0.6 (random scene のみ trigger) | `D_residual` > 0.005 (Stage C undershoot 経) |
| F5 | Cosserat local minima | `D_residual` > 0.005 | `D_iter_count` >= 200 (timeout) |
| F6 | Identity inversion | `identity_inversion_count` ≥ 1 (Q5 Gate 5 fail trigger) | `D_residual` > 0.002 (warn) |
| F7 | Latency overflow | `Total_latency` > 0.05 (50ms) | `D_iter_count` > 150 |
| F8 | NaN segment propagation | `nan_segment_count` ≥ 5 in scene | `B_bin_emptiness` > 8 |
| F9 | Cloud expose API gap | `Total_latency` > 0.10 (100ms、estimate_with_cloud overhead 経) | (Phase 5 impl で wrapper 漏れ trigger) |
| F10 | Stage C checkpoint missing | RuntimeError at `CableStateSolver.__init__` (eval pipeline 起動失敗) | (binary check、threshold fail 経で attribution 不要、early exit) |
| F11 | Phase 番号 renumber 混乱 | (operational issue、metric attribution 不適用) | (本 leaf §1.4 + state.md §1 + manifest §運用注 で永続化) |
| F12 | per-stage diagnostics schema drift | Phase 7 schema compliance test FAIL | (本 §6 schema lock 経で防止) |

### §7.2 Primary cause classification

```python
def attribute_failure(
    per_scene_metrics: list[Q5SceneMetrics],
    gates: dict[str, bool],
) -> tuple[str | None, list[str]]:
    """Attribute Q5 failure to primary F mode + secondary list (本 leaf 新規 spec)."""
    failed_gates = [g for g, p in gates.items() if not p]

    # Map failed gates to F modes
    gate_to_F = {
        "random_mean_error_lt_5mm": ["F1", "F2", "F3", "F4", "F5"],  # random scene の error 大 → 主 stage A-D issue
        "random_p95_error_lt_10mm": ["F3", "F4", "F5", "F8"],
        "ushape_all_lt_5mm":        ["F4", "F5"],  # U-shape は PCA fail + Cosserat local min が主因
        "sshape_all_lt_5mm":        ["F4", "F5"],
        "zero_identity_inversion":  ["F6"],
        "ece_lt_5pct":              ["F8"],  # confidence calibration issue → NaN propagation 経
        "latency_p95_lt_50ms":      ["F7", "F9"],
    }

    # Tally F mode candidates from failed gates
    F_candidates = []
    for gate in failed_gates:
        F_candidates.extend(gate_to_F.get(gate, []))

    # Per-stage diagnostics aggregation で actual stage threshold violation count を確認
    stage_reports = aggregate_stage_diagnostics(per_scene_metrics)
    stage_fail_counts = {r.metric_name: r.n_fail_scenes for r in stage_reports}

    # F mode → stage threshold linkage で actual fail 経の F mode 確定
    F_actual = []
    F_to_stage = {
        "F1": ["A_per_cam_iou"],
        "F2": ["A_n_pts"],
        "F3": ["B_bin_emptiness"],
        "F4": ["B_var_ratio_random"],
        "F5": ["D_residual", "D_iter_count"],
        "F6": [],  # identity_inversion は per-scene metric (gates "zero_identity_inversion" 経で検出済)
        "F7": ["Total_latency"],
        "F8": [],  # nan_segment_count は per-scene metric
        "F9": ["Total_latency"],  # latency 100ms+ で trigger
    }
    for F_mode in set(F_candidates):
        if F_mode in ("F6", "F8"):  # always include if gate failed
            F_actual.append(F_mode)
        else:
            stage_keys = F_to_stage.get(F_mode, [])
            if any(stage_fail_counts.get(k, 0) > 0 for k in stage_keys):
                F_actual.append(F_mode)

    if not F_actual:
        return ("F-unknown", [])  # gate failed but no stage threshold linkage 経 → 調査要 (data integrity etc.)

    # Tie-breaking: stage 順 (A→B→C→D→E) で earlier stage primary
    stage_order = {"F1": 1, "F2": 1, "F3": 2, "F4": 2, "F5": 4, "F6": 5, "F7": 6, "F8": 4, "F9": 6}
    F_actual_sorted = sorted(set(F_actual), key=lambda f: stage_order.get(f, 99))

    primary = F_actual_sorted[0]
    secondary = F_actual_sorted[1:]
    return (primary, secondary)
```

### §7.3 Tie-breaking rule rationale

- **Stage 順 (A→B→C→D→E)**: earlier stage failure は downstream stage failure の root cause になりやすい (例: Stage A `n_pts < 800` → Stage B `var_ratio < 0.6` cascade)
- **Single-cause vs multi-cause**: primary = top-1 stage failure、secondary = 残り (Phase 4 §8 OQ-P4-10 spec)
- **F-unknown 出力**: gate failed but stage threshold linkage 経 不一致時 → Phase 7 で manual 調査 trigger (data integrity / measurement bug 等)

---

## §8 Ablation study spec (本 leaf 新規)

### §8.1 4 axis spec

| axis | cells | rationale | hooks (Phase 5-6 impl spec) |
|------|-------|-----------|------------------------------|
| Stage C on/off | 2 cells: `--use-stage-c` (default) / `--no-stage-c` | DD-PINN warm start の incremental value 測定 | Phase 5 (Stage C train) で `--use-stage-c` flag、Phase 6 (Stage D/E impl) で `CableStateSolverConfig.bypass_stage_c: bool = False` field 追加 |
| Multi-restart count | 5 cells: 1 / 2 / 3 / 4 / 5 (default 5) | Phase 3 OQ-P3-9 + Phase 2 §3.5 既存 spec、5-restart の incremental value 測定 | Phase 6 (Stage D impl) で `CosseratSolverConfig.multi_restart_count: int = 5` field 追加 |
| Stage E calibration on/off | 2 cells: `--enable-confidence-calibration` (default) / `--disable-confidence-calibration` | logistic regression coefficient の incremental value 測定 (uncalibrated 0.5 fallback と比較) | Phase 6 (Stage E impl) で `CableStateSolverConfig.calibrated_confidence: bool = True` field 追加 |
| var_ratio threshold | 5 cells: 0.50 / 0.55 / 0.60 (default) / 0.65 / 0.70 | Phase 3 OQ-P3-2 spec、Stage C trigger sensitivity 測定 | (既存 `CableStateSolverConfig.var_ratio_threshold = 0.6` field、新規 hook 不要) |

**Total cells**: 2 × 5 × 2 × 5 = 100 cells (axis 全 sweep)。

### §8.2 GPU budget

| protocol | cell count | seed count | scene count | per-scene latency | total wall |
|----------|-----------|-----------|-------------|-------------------|------------|
| Full sweep | 100 cells | 5 seeds | 120 scenes | ~50ms | ~100 × 5 × 120 × 0.05s ≈ 3000s ≈ 50 min wall single-process |
| Reduced sweep (axis 独立 sweep) | 14 cells (2+5+2+5) | 5 seeds | 120 scenes | ~50ms | 14 × 5 × 120 × 0.05s ≈ 420s ≈ 7 min wall |
| Minimum-viable subset | 4 cells (1 axis × 1 cell × 5 seeds) | 5 seeds | 120 scenes | ~50ms | 4 × 5 × 120 × 0.05s ≈ 120s ≈ 2 min wall |

**注**: 上記は single-process estimate。GPU device load + L-BFGS overhead 経で 5-10x slower 想定 (実測 wall は ~5-50 min for minimum-viable, ~5-8h for reduced sweep, ~10-16h for full sweep)。

### §8.3 Minimum-viable subset (Phase 7 必須)

Phase 7 起票時、Rs explicit GPU schedule 経で minimum subset run 必須:

```
Cell 1: default config (Stage C ON, restart=5, calibration ON, var_ratio=0.60) × 5 seeds
Cell 2: --no-stage-c (Stage C OFF, others default) × 5 seeds
Cell 3: --multi-restart-count 1 (restart=1, others default) × 5 seeds
Cell 4: --disable-confidence-calibration (calibration OFF, others default) × 5 seeds
```

**Goal**: Stage C / multi-restart / Stage E calibration の 3 軸 incremental value baseline 確認、~5 min × 5 ≈ ~30 min wall。

### §8.4 Full sweep (optional、Phase 8 別 leaf 候補)

Full sweep (100 cells × 5 seeds × 120 scenes ≈ ~10-16h GPU) は別 leaf `T-Vision-CableState-Impl-Phase-8-Full-Ablation` で起票候補:
- trigger: Phase 7 minimum subset PASS + Rs explicit GPU schedule + sensitivity analysis priority
- defer 理由: Phase 7 verdict (Q5 PASS / FAIL) は minimum subset で十分、full sweep は post-mortem analysis 用

### §8.5 Ablation report format

```python
@dataclass
class AblationReport:
    """Per-cell ablation result."""
    cell_id: str                          # "default" | "no_stage_c" | "restart_1" | etc.
    config_overrides: dict[str, Any]      # 上 §8.1 hooks 対応の override fields
    seed_results: list[Q5BenchVerdict]    # per-seed verdicts (5 entries)

    # Aggregated metrics (mean / std across 5 seeds)
    mean_random_error: float
    std_random_error: float
    mean_ushape_pass_rate: float          # = sum(ushape_passed for seed) / 5
    mean_ece: float

    # Comparative analysis vs default cell
    delta_vs_default: dict[str, float]    # {metric: delta} (default cell との差分)
```

---

## §9 Ground truth comparison protocol (本 leaf 新規)

### §9.1 Newton state dump → 40-segment GT

```python
def dump_cable_ground_truth(env: "NewtonEnv", batch_idx: int = 0) -> torch.Tensor:
    """Dump 40-segment cable ground truth from Newton env state.

    Args:
        env: Newton VBD env instance (cable scene loaded).
        batch_idx: scene batch index (Phase 7 では per-scene serial、batch_idx=0).

    Returns:
        ground_truth: [40, 3] world-frame xyz [m]、float32 / float64.

    R6 boundary: env-side acquisition のみ、estimator core 内では `EstimatorLabelsForEvalOnly`
    boundary 経で smuggling 防止 (parent §6.3)。本 function は eval pipeline 内 newton-side でのみ呼ばれる。
    """
    # Newton VBD 内 cable body は ArticulationView 経で query (LL-Newton.md spec)
    # cable には CABLE_SEGMENTS=40 segments、各 segment が rigid body + ball joint chain
    cable_view = env.scene["cable"]
    body_q = cable_view.body_q  # [num_envs, num_bodies, 7] (px, py, pz, qx, qy, qz, qw)
    # Note: cable num_bodies は CABLE_SEGMENTS + 1 (head + 40 segments)、segment_idx=1..40 が cable segments
    # 本 spec では segment_idx=1..40 を P_seg(0)..P_seg(39) と mapping (handedness 統一)
    seg_positions = body_q[batch_idx, 1:41, 0:3]  # [40, 3] world-frame xyz
    return seg_positions.clone().detach()  # disconnect from autograd graph (eval-only)
```

### §9.2 GT acquisition R6 boundary preservation

```
estimator core (CableStateSolver, MultiCamCableStatePipeline)
  - inputs: EstimatorInputs (rgb / depth / cam_poses / intrinsics / finger_positions)
  - NO access to env.scene["cable"].body_q (R6 forbidden)
  - output: CableState40 (per-stage diagnostics + position estimates)

eval pipeline (Phase 7、env-side wrapper)
  - dump GT via dump_cable_ground_truth(env)  → ground_truth ∈ ℝ^(40, 3)
  - run estimator → cable_state ∈ CableState40
  - compute per_seg_errors = ‖cable_state.positions - ground_truth‖₂
  - GT 経 path は eval pipeline scope only、estimator core 内 不在
```

### §9.3 GT validation checks

Phase 7 起票時、GT acquisition 経 data integrity check:

```python
def validate_ground_truth(gt: torch.Tensor) -> tuple[bool, str]:
    """Validate GT integrity (Phase 7 reference)."""
    if gt.shape != (40, 3):
        return (False, f"shape mismatch: expected (40, 3), got {tuple(gt.shape)}")
    if torch.isnan(gt).any():
        return (False, f"NaN found in GT (count: {torch.isnan(gt).sum().item()})")
    # Per-segment distance check: arc-length should be ~CABLE_SEG_LEN (15mm) per segment
    seg_dists = torch.norm(gt[1:] - gt[:-1], dim=-1)  # [39]
    median_seg_dist = seg_dists.median().item()
    if not (0.010 < median_seg_dist < 0.020):  # 10-20mm acceptable range (sim cable nominal 15mm)
        return (False, f"median segment distance {median_seg_dist:.4f}m outside [10mm, 20mm]")
    # World-frame position bounds check (table center ~ (0.3, 0.0, 0.8), cable extent < 1m)
    pos_max = gt.max(dim=0).values
    pos_min = gt.min(dim=0).values
    extent = pos_max - pos_min
    if extent.max().item() > 2.0:  # > 2m extent suspicious
        return (False, f"GT extent {extent.tolist()}m suspicious")
    return (True, "GT valid")
```

### §9.4 GT acquisition timing

| scene type | timing | rationale |
|------------|--------|-----------|
| random | sampling 時 (held-out replay log の各 snapshot で env state dump 経 GT pre-computed、Q5SceneSpec.ground_truth に embed) | 1-time cost (sampling phase)、Phase 7 eval は ground_truth read のみ |
| ushape | scripted scene generation 時 (Step 4 snapshot 後 dump_cable_ground_truth) | 1-time cost (scene generation phase)、Phase 7 eval は read のみ |
| sshape | 同上 | 同上 |

### §9.5 Per-segment ordering convention

P_seg(0) は handedness anchor 経で定まる (Phase 1 §3.5 + Phase 3 §3.3)。GT も同 convention 適用:
- grasp active: P_seg(0) = grasp finger 側 segment
- no grasp: P_seg(0) = episode-start prior の handedness anchor (newton env initial pose で fixed)

**注**: identity inversion check (§4.2) は P̂_seg と GT の reversed direction 比較で検出、本 ordering convention 不一致時 false-positive trigger。Phase 7 で per-scene handedness validation 必要。

---

## §10 Reporting format spec (Phase 3 §5.5 拡張)

### §10.1 Per-scene CSV schema

`q5_per_scene_metrics.csv` (Phase 7 で生成):

| column | dtype | source |
|--------|-------|--------|
| `scene_id` | string | Q5SceneMetrics.scene_id |
| `scene_type` | string ("random" / "ushape" / "sshape") | Q5SceneMetrics.scene_type |
| `mean_error_m` | float64 | Q5SceneMetrics.mean_error_m |
| `p95_error_m` | float64 | Q5SceneMetrics.p95_error_m |
| `max_error_m` | float64 | Q5SceneMetrics.max_error_m |
| `identity_inversion` | bool | Q5SceneMetrics.identity_inversion |
| `has_nan_segments` | bool | Q5SceneMetrics.has_nan_segments |
| `nan_segment_count` | int64 | Q5SceneMetrics.nan_segment_count |
| `total_latency_ms` | float64 | Q5SceneMetrics.total_latency_ms |
| `stage_a_b_latency_ms` | float64 | Q5SceneMetrics.stage_a_b_latency_ms |
| `stage_a3_n_pts` | int64 | stage_diagnostics["stage_a3"]["n_pts"] |
| `stage_b_var_ratio` | float64 | stage_diagnostics["stage_b"]["var_ratio"] |
| `stage_b_bin_emptiness` | int64 | sum(c == 0 for c in stage_diagnostics["stage_b"]["bin_counts"]) |
| `stage_c_triggered` | bool | stage_diagnostics["stage_c_triggered"] |
| `stage_c_latency_ms` | float64 (NaN if not triggered) | stage_diagnostics["stage_c"]["latency_ms"] if triggered else NaN |
| `stage_d_final_loss` | float64 | stage_diagnostics["stage_d"]["final_loss"] |
| `stage_d_iter_count` | int64 | stage_diagnostics["stage_d"]["iter_count"] |
| `stage_d_restart_used` | int64 (0..4) | stage_diagnostics["stage_d"]["restart_used"] |
| `stage_d_latency_ms` | float64 | stage_diagnostics["stage_d"]["latency_ms"] |
| `identity_inversion_detected` | bool | stage_diagnostics["identity_inversion_detected"] |
| `stage_e_latency_ms` | float64 | stage_diagnostics["stage_e"]["latency_ms"] |
| `fallback_reason` | string (NaN if not fallback) | stage_diagnostics.get("fallback") |

**dtype enforcement**:

```python
# Phase 7 で生成時 dtype enforce:
dtype_dict = {
    "scene_id": "string", "scene_type": "string",
    "mean_error_m": "float64", "p95_error_m": "float64", "max_error_m": "float64",
    "identity_inversion": "bool", "has_nan_segments": "bool",
    "nan_segment_count": "int64",
    "total_latency_ms": "float64", "stage_a_b_latency_ms": "float64",
    "stage_a3_n_pts": "int64",
    "stage_b_var_ratio": "float64", "stage_b_bin_emptiness": "int64",
    "stage_c_triggered": "bool", "stage_c_latency_ms": "float64",
    "stage_d_final_loss": "float64", "stage_d_iter_count": "int64",
    "stage_d_restart_used": "int64", "stage_d_latency_ms": "float64",
    "identity_inversion_detected": "bool", "stage_e_latency_ms": "float64",
    "fallback_reason": "string",
}
# pandas.DataFrame(data).astype(dtype_dict).to_csv(...)
```

### §10.2 Q5 verdict JSON schema

`q5_verdict.json` (Phase 7 で生成):

```json
{
  "schema_version": "1.0",
  "overall_passed": true,
  "per_gate_status": {
    "random_mean_error_lt_5mm": true,
    "random_p95_error_lt_10mm": true,
    "ushape_all_lt_5mm": true,
    "sshape_all_lt_5mm": true,
    "zero_identity_inversion": true,
    "ece_lt_5pct": true,
    "latency_p95_lt_50ms": true
  },
  "metrics": {
    "random_mean_error_m": 0.0042,
    "random_p95_error_m": 0.0089,
    "ushape_mean_errors_m": [0.0044, 0.0048, 0.0046, 0.0049, 0.0043, 0.0045, 0.0047, 0.0044, 0.0046, 0.0048],
    "sshape_mean_errors_m": [0.0046, 0.0049, 0.0047, 0.0048, 0.0045, 0.0047, 0.0049, 0.0046, 0.0048, 0.0047],
    "identity_inversion_count": 0,
    "overall_ece": 0.038,
    "latency_p95_ms": 47.3
  },
  "failure_attribution": {
    "primary_failure_cause": null,
    "secondary_failure_causes": []
  },
  "scene_counts": {
    "n_random_scenes": 100,
    "n_ushape_scenes": 10,
    "n_sshape_scenes": 10,
    "n_excluded_scenes": 0
  },
  "metadata": {
    "commit_sha": "abc1234",
    "dataset_sha256": "def5678...",
    "checkpoint_sha256": "ghi9012...",
    "phase5_train_hyperparams": {
      "lr": 1e-3, "batch_size": 32, "epochs": 100, "optimizer": "Adam"
    },
    "phase6_impl_sha": "jkl3456",
    "eval_run_timestamp": "2026-XX-XX T XX:XX:XX +09:00",
    "eval_machine": "rlrk-IsaacLab",
    "gpu_device": "cuda:2",
    "gpu_name": "RTX PRO 4000 Blackwell 24GB",
    "cudnn_deterministic": true,
    "global_seed": 42,
    "python_version": "3.11.x",
    "torch_version": "2.x.x"
  }
}
```

### §10.3 JSON schema validation

Phase 7 で生成 JSON validation 用の schema (jsonschema library 経で検証):

```python
Q5_VERDICT_JSON_SCHEMA = {
    "type": "object",
    "required": ["schema_version", "overall_passed", "per_gate_status", "metrics", "failure_attribution", "scene_counts", "metadata"],
    "properties": {
        "schema_version": {"type": "string", "const": "1.0"},
        "overall_passed": {"type": "boolean"},
        "per_gate_status": {
            "type": "object",
            "required": ["random_mean_error_lt_5mm", "random_p95_error_lt_10mm", "ushape_all_lt_5mm",
                         "sshape_all_lt_5mm", "zero_identity_inversion", "ece_lt_5pct", "latency_p95_lt_50ms"],
        },
        # ... (full schema in Phase 7 impl reference)
    },
}
```

### §10.4 Summary md template

`q5_summary.md` (Phase 7 で生成):

```markdown
# Q5 Cable State Estimation Benchmark Verdict

**Date**: 2026-XX-XX
**Commit**: abc1234 / Checkpoint: ghi9012 (Phase 5 train) / Impl SHA: jkl3456 (Phase 6 impl)
**GPU**: cuda:2 (RTX PRO 4000 Blackwell 24GB) — cudnn deterministic mode
**Eval Dataset**: 120 scenes (100 random + 10 U-shape + 10 S-shape)

## Overall Verdict

| Status | Value |
|--------|-------|
| Overall PASS | ✅ True (or ❌ False) |

## Per-Gate Status

| Gate | Status | Value | Threshold |
|------|--------|-------|-----------|
| random_mean_error_lt_5mm | ✅ | 4.2 mm | < 5 mm |
| random_p95_error_lt_10mm | ✅ | 8.9 mm | < 10 mm |
| ushape_all_lt_5mm        | ✅ | all 10 / 10 < 5 mm | individual compliance |
| sshape_all_lt_5mm        | ✅ | all 10 / 10 < 5 mm | individual compliance |
| zero_identity_inversion  | ✅ | 0 / 120 | == 0 |
| ece_lt_5pct              | ✅ | 3.8% | < 5% |
| latency_p95_lt_50ms      | ✅ | 47.3 ms | < 50 ms |

## Failure Attribution (if not PASS)

- Primary cause: F-X (description)
- Secondary causes: F-Y, F-Z

## Per-Stage Diagnostics Top-3 Concerns

(if any) - Stage X metric Y exceeded warn threshold in Z scenes

## Reproducibility

- Global seed: 42
- Per-restart seed: seed_base + restart_idx
- bit-identical reproducible: ✅ Yes (5-run check passed)
```

### §10.5 Output directory structure

```
output_dir/
├── q5_verdict.json              # Q5BenchVerdict serialized (本 §10.2)
├── q5_per_scene_metrics.csv     # per-scene metrics (本 §10.1)
├── q5_stage_diagnostics.json    # per-stage Q5StageDiagnosticsReport (本 §6.3)
├── q5_summary.md                # human-readable summary (本 §10.4)
├── q5_eval_dataset_metadata.json # Q5SceneSpec metadata (excluding inputs/GT tensors、reproducibility 用)
└── ablation/                    # ablation study results (本 §8、optional)
    ├── default/q5_verdict.json
    ├── no_stage_c/q5_verdict.json
    ├── restart_1/q5_verdict.json
    └── ...
```

---

## §11 Reproducibility checklist (本 leaf 新規)

### §11.1 EvalRunMetadata schema

```python
@dataclass(frozen=True)
class EvalRunMetadata:
    """Reproducibility metadata embedded in Q5BenchVerdict (本 leaf 新規 spec、Phase 7 まで UNCHANGED)."""
    # Code versioning
    commit_sha: str                       # git rev-parse HEAD (current branch)
    branch_name: str                      # e.g., "develop"

    # Dataset versioning
    dataset_sha256: str                    # hash of eval dataset (Q5SceneSpec list serialized)
    dataset_n_scenes: int                  # = 120 expected

    # Checkpoint versioning
    checkpoint_sha256: str                 # hash of Stage C DD-PINN checkpoint .pt file
    checkpoint_path: str                   # absolute path to checkpoint file
    checkpoint_phase5_train_hyperparams: dict[str, Any]  # train config used

    # Impl versioning (Phase 6 = Stage D/E impl)
    phase6_impl_sha: str                   # git commit SHA of Phase 6 impl

    # Runtime environment
    eval_run_timestamp: str                # ISO 8601 with timezone
    eval_machine: str                      # hostname
    gpu_device: str                        # "cuda:2" (or CPU if fallback)
    gpu_name: str                          # nvidia-smi --query
    cudnn_deterministic: bool              # True for canonical run
    global_seed: int                       # = 42
    python_version: str                    # sys.version
    torch_version: str                     # torch.__version__
    numpy_version: str                     # np.__version__

    # Hardware fingerprint
    cuda_visible_devices: str              # CUDA_VISIBLE_DEVICES env var
    cuda_arch: str                         # torch.cuda.get_device_capability()

    # Eval pipeline config
    n_restarts: int                        # = 5 (default、ablation で override 可)
    var_ratio_threshold: float             # = 0.6 (default)
    use_stage_c: bool                      # = True (default)
    use_calibrated_confidence: bool        # = True (default)
```

### §11.2 Reproducibility checklist (15+ items)

Phase 7 起票時に確認 + verdict JSON metadata field に embed:

1. ☐ commit SHA (current branch HEAD)
2. ☐ branch name
3. ☐ dataset hash (Q5SceneSpec list serialized SHA-256)
4. ☐ dataset scene count (= 120 expected)
5. ☐ Stage C checkpoint hash (Phase 5 train output .pt file SHA-256)
6. ☐ Stage C checkpoint absolute path
7. ☐ Stage C checkpoint Phase 5 train hyperparameters (lr, batch_size, epochs, optimizer, ...)
8. ☐ Phase 6 impl commit SHA (Stage D + E impl + cable_state.py orchestrator delegate)
9. ☐ eval run timestamp (ISO 8601 + timezone)
10. ☐ eval machine hostname
11. ☐ GPU device (`cuda:2` for canonical)
12. ☐ GPU name (nvidia-smi query)
13. ☐ cudnn deterministic mode (= True for canonical)
14. ☐ global random seed (= 42)
15. ☐ Python + PyTorch + NumPy versions
16. ☐ CUDA_VISIBLE_DEVICES env var
17. ☐ CUDA architecture (compute capability)
18. ☐ Eval pipeline config (n_restarts, var_ratio_threshold, use_stage_c, use_calibrated_confidence)

### §11.3 5-run reproducibility test (Phase 7 reference)

```python
def test_q5_5_run_reproducibility(eval_dataset, pipeline, estimator):
    """Q5 verdict が 5 run で identical (Phase 4 §3.4 spec の Phase 7 enforcement)."""
    verdicts = []
    for run_idx in range(5):
        # Reset all random states
        random.seed(42)
        np.random.seed(42)
        torch.manual_seed(42)
        torch.cuda.manual_seed(42)

        verdict, _ = run_q5_benchmark(
            pipeline, estimator, eval_dataset,
            output_dir=f"/tmp/q5_run_{run_idx}",
        )
        verdicts.append(verdict)

    # Check all overall_passed identical
    assert len(set(v.overall_passed for v in verdicts)) == 1, "overall_passed mismatch across runs"

    # Check metric drift within ε=1e-6 (line search non-determinism 経 minor difference)
    metrics_to_check = ["random_mean_error_m", "random_p95_error_m", "overall_ece", "latency_p95_ms"]
    for metric in metrics_to_check:
        values = [getattr(v, metric) for v in verdicts]
        drift = max(values) - min(values)
        assert drift < 1e-6, f"{metric} drift {drift} across runs (>{1e-6} threshold)"
```

---

## §12 Phase 7 prerequisite + spec source pointer

### §12.1 Phase 7 起票 trigger (本 leaf §8 spec の Phase 7 reference)

| precondition | mechanism | external dependency | spec source |
|--------------|-----------|---------------------|-------------|
| 本 Phase 4 validation design COMPLETE | leaf state.md status COMPLETE | (本 leaf 完走) | (本 design memo) |
| Phase 5 (Stage C train) COMPLETE | DD-PINN checkpoint 生成 + checkpoint hash 確定 | T-Vision-DR-Impl-Phase0 cascade + ~25h GPU | Phase 3 §8.1 + 本 §1.4 renumber |
| Phase 6 (Stage D/E impl) COMPLETE | `cable_state.py` `CableStateSolver` orchestrator delegate fill + Stage D/E impl ready | (immediate post Phase 5) | Phase 3 §8.2 + 本 §1.4 renumber |
| 10 U-shape + 10 S-shape scripted scene generator ready | env-side scripted scenarios impl (本 §2.3 + §2.4 spec 経で newton env scripting) | env-side eng (~3-5h) | 本 §2.3 + §2.4 |
| N=100 random held-out scenes generation | env-side replay sampling impl (本 §2.2 spec) | (immediate、existing replay infrastructure 経) | 本 §2.2 |
| Q5 gate execution + ECE measurement + identity inversion 0% verify + latency p95 <50ms verify | 本 design memo § 全 (eval mode + ground truth + per-scene metric + PASS criteria + failure attribution + reporting format) を spec source として実装 | (本 design memo を spec source として Phase 7 で reference) | 本 §3-§11 |
| Ablation study minimum-viable subset run | 本 §8.3 spec 経 (4 cells × 5 seeds、~30 min wall) | (Rs explicit GPU schedule) | 本 §8.3 |

### §12.2 Phase 5-6 起票時の本 leaf spec source 用法

| Phase | section | usage |
|-------|---------|-------|
| Phase 5 (Stage C train) | 本 §8 ablation hooks | Stage C train script に `--use-stage-c` flag (default ON、ablation で OFF 可) を impl |
| Phase 5 (Stage C train) | 本 §3.2 per-restart seed | (Stage C train は per-restart 不要、Phase 6 Stage D Cosserat 用 spec) |
| Phase 6 (Stage D impl) | 本 §3.2 per-restart seed | `cosserat_multi_restart_fit` impl で `derive_restart_seed` 経 |
| Phase 6 (Stage E impl) | 本 §5.4 ECE computation | logistic regression coefficient calibration 後 `compute_global_ece` で ECE measure |
| Phase 6 (impl) | 本 §6.4 `_extract_metric_from_diagnostics` | `cable_state.py` `CableStateSolver._stage_*` で diagnostics dict population spec、本 §6.4 mapping と一致 enforce |
| Phase 6 (impl) | 本 §8.1 ablation hooks | `CableStateSolverConfig` に `bypass_stage_c`、`calibrated_confidence` field 追加 (Phase 6 impl) |

---

## §13 Cross-references + output format compliance + status

### §13.1 Internal vault

- **Parent design memo**: `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md` (769 行、approved 2026-05-03、§1 (target metric) + §3 (topology) + §5 (benchmark) + §6 (R6 boundary) spec source)
- **Sibling Phase 1 state**: `thread_isaac_lab/thread-vault/T-Vision-CableState-Impl-Phase-1/state.md` (COMPLETE 2026-05-04T03:50)
- **Sibling Phase 2 design memo**: `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase2-Impl-Design.md` (~820 行、design 2026-05-04、§2 (Stage C) + §3 (Stage D) + §4 (Stage E) + §5 (Phase 1 → Phase 2 component-level integration) spec source)
- **Sibling Phase 3 design memo**: `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase3-Integration-Design.md` (~1100 行、design 2026-05-04、§3 (orchestration) + §5 (Q5 protocol initial) + §6 (latency budget) + §7 (failure mode F1-F12) spec source、本 leaf §5-§7 finalize 起点)
- **Sibling Phase 3 state**: `thread_isaac_lab/thread-vault/T-Vision-CableState-Impl-Phase-3-Integration-Design/state.md`
- **Parent NEST node**: `thread_isaac_lab/thread-vault/T-Vision-CableState/state.md`
- **CC4 v3.2 base spec**: `thread_isaac_lab/thread-vault/07-Design/PoseEstimation-Design-v3.2.md` §H Estimator boundary、§10 (eval mode + cuda:2 deterministic kernel)、§6.4 Late Fusion downstream
- **R6 boundary tests**: `thread_isaac_lab/tests/test_estimator_input_boundary.py` + `tests/test_estimator_module_boundary.py` + `tests/test_cable_state_phase1.py` + `tests/test_cable_state_phase2_skeleton.py`
- **EXP-046 baseline**: `thread-vault/05-Thinking/Experiment Log.md` L1673-1686 (PCA-center 3.92mm @ single-midpoint, 1635 merged pts, 3-cam) — 本 leaf §0 + parent §0 reference

### §13.2 Code references (本 leaf 参照のみ、改変なし)

- `thread_isaac_lab/configs/task_config.py:70-75` — CABLE_SEGMENTS=40, CABLE_SEG_LEN=0.015, CABLE_RADIUS=0.004, CABLE_BEND_STIFFNESS=0.1 (本 §9 GT validation 経 reference)
- `thread_isaac_lab/models/vision_pipeline.py` — Phase 1 完成 API (`MultiCamCableStatePipeline`、本 §4 evaluate_scene 経 reference)
- `thread_isaac_lab/envs/wrist_camera_manager.py` — Phase 1 完成 API (`CableStateCameraManager`、本 §3 eval mode reference)
- `thread_isaac_lab/estimators/cable_state.py` — Phase 6 impl scope (`CableStateSolver`、本 §3.6 + §4.1 reference)
- `thread_isaac_lab/estimators/cable_state_dd_pinn.py` — Phase 2 skeleton (本 §8 ablation hooks reference)
- `thread_isaac_lab/estimators/cable_state_cosserat.py` — Phase 2 skeleton (本 §3.2 per-restart seed + §8 ablation hooks reference)
- `thread_isaac_lab/estimators/cable_state_confidence.py` — Phase 2 skeleton (本 §5.4 + §8 ablation hooks reference)
- `thread_isaac_lab/estimators/types.py` — `CableState40` (本 §4 Q5SceneMetrics consume reference) + `EstimatorInputs` (本 §2.5 Q5SceneSpec embed reference) + `EstimatorLabelsForEvalOnly` (本 §9 R6 boundary reference)

### §13.3 Sister leaves & downstream

- **T-Vision-Pose** (L1.A.1 precedent edge、Stage A-B substrate 共有): `thread-vault/T-Vision-Pose/state.md`
- **T-Vision-DR** (L1.A.3、shared dataset re-render asset、Phase 5 train で 5k labeled dataset cascade): `thread-vault/T-Vision-DR/state.md`
- **T-Vision-Fusion** (L1.A.4 downstream consumer、cable_state 120D obs 統合): `thread-vault/T-Vision-Fusion/state.md`
- **T-Vision umbrella**: `thread-vault/T-Vision/state.md`
- **T-Vision-L1A-Master-Integration-Design** (cross-cutting integration view、本 leaf も入力 candidate): `thread-vault/T-Vision-L1A-Master-Integration-Design/state.md`

### §13.4 Output format compliance (CLAUDE.md §運用)

| 区分 | 主張 | 根拠（出典） |
|------|------|---------------|
| 事実 | parent design memo §1.1 で "deterministic (seed=42, cuda:2 deterministic kernel)" 既存 spec | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md:42-52` |
| 事実 | Phase 3 design memo §5.1 で N=100 + 10U + 10S total 120 scenes spec | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase3-Integration-Design.md:652-658` |
| 事実 | Phase 3 design memo §5.3 で 7 gates (random_mean<5mm + random_p95<10mm + ushape 10/10 + sshape 10/10 + identity_inversion=0 + ECE<5% + latency_p95<50ms) | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase3-Integration-Design.md:798-862` |
| 事実 | Phase 3 design memo §5.4 で per-stage thresholds 10 entries (A_n_pts / A_per_cam_iou / B_var_ratio_random / B_bin_emptiness / C_warm_mse / C_latency / D_residual / D_iter_count / E_ece / Total_latency) | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase3-Integration-Design.md:866-902` |
| 事実 | Phase 3 design memo §6.1 で per-stage latency budget A:5/B:5/C:2/D:30/E:5/Identity:3 = 50ms total | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase3-Integration-Design.md:932-940` |
| 事実 | Phase 3 design memo §3.4 で stage_diagnostics dict schema (stage_a3, stage_b, stage_c_triggered, stage_c, stage_d, identity_inversion_detected, stage_e, total_latency_ms) | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Phase3-Integration-Design.md:511-563` |
| 事実 | parent design memo §1.4 で existing assets (vision_pipeline.py 264 LoC + wrist_camera_manager.py ~210 LoC + estimators/types.py + task_config.py:70-75) | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md:69-79` |
| 事実 | parent design memo §6.3 で `EstimatorLabelsForEvalOnly` boundary 経で newton state smuggling 防止 spec | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md:628-634` |
| 推測 | bit-identical reproducibility は cuda:2 deterministic kernel + per-restart seed 経で達成可能、PyTorch L-BFGS line search 経の minor non-determinism は ε=1e-6 within | PyTorch docs (cudnn deterministic mode + manual_seed) + L-BFGS line search uses seed-derived ε-perturbation。Phase 7 で empirical 5-run check 経で確認 |
| 推測 | 全 ablation full sweep 100 cells × 5 seeds × 120 scenes ≈ ~10-16h GPU、minimum-viable subset 4 cells × 5 seeds ≈ ~30 min wall | 本 §8.2 GPU budget 推定 (per-scene ~50ms + L-BFGS overhead 5-10x slower 想定)、empirical wall は Phase 7 で実測 |
| 推測 | 5+ 連続 NaN segments 観察時 Stage C trigger 拡張 (`var_ratio < 0.6 OR consecutive_nan ≥ 5`) は Phase 7 で empirical revise candidate | Phase 3 §2.3 + 本 §4.3 NaN handling spec、Phase 7 観察時 trigger condition 拡張 (本 leaf scope 外、Phase 7 で empirical decision) |
| 推測 | Q5 verdict CSV downstream consumption は pandas を想定、parquet alternative は依存追加 cost (pyarrow ~50MB) > 価値 (本 leaf データ量 ~120 row) | 本 §10.1 + §8 OQ-P4-5 disposition |
| 推測 | failure attribution multi-cause concurrency 観察時 root-cause analysis 拡張は Phase 7 ambiguity 観察 経 | 本 §7 + §8 OQ-P4-3 disposition、現 spec は primary + secondary 2-tier、Phase 7 で 3-tier 拡張候補 |

### §13.5 Status

- **Created**: 2026-05-04T14:05:00+09:00 (T-Vision-CableState-Impl-Phase-4-Validation-Design-CC sub-session)
- **Phase**: design (本 leaf scope = validation methodology + benchmark protocol final design only、impl + train + benchmark execution は Phase 5-7 別 NEST node)
- **Author**: T-Vision-CableState-Impl-Phase-4-Validation-Design-CC (sub-agent of T-ROOT-COORD)
- **Permissions**: 06-Knowledge は CC Create/Update 可 (Vault Write Permissions)
- **Next steps (Phase 5+ trigger)**:
  - 本 Phase 4 validation design + benchmark protocol final COMPLETE
  - Phase 5 (Stage C train、~25h GPU + 5k labeled dataset prerequisite) 起票候補 — T-Vision-DR-Impl-Phase0 cascade + Rs §3.1 #4 起動承認待ち
  - Phase 6 (Stage D Cosserat impl + Stage E ECE calibration) 起票候補 — Phase 5 PASS + 1k val held-out 経
  - Phase 7 (Q5 worst-case benchmark execution) 起票候補 — Phase 6 COMPLETE + 10U/10S scripted scene env-side ready 経
- **04-Specs SSOT update**: out-of-scope (Rs専権 per Vault Write Permissions); Rs 承認後 separate task で起票候補

---

## §14 Phase 4 deliverable checklist (acceptance gate、state.md §10 同期)

design 観点の acceptance:
- [x] design memo §0-§13 全 section 起票、各 section が Phase 3 §5 を implementation-ready level に finalize している (重複でなく細密化、本 §1.5 per-section ownership matrix 経で differentiation 明示)
- [x] eval mode protocol (deterministic seed + cuda:2 kernel + multi-restart determinism + batch sizing) implementation-ready (本 §3)
- [x] ground truth comparison protocol (newton state dump → 40-segment GT → metric pipeline) spec (本 §9)
- [x] per-scene metric implementation-ready (Q5SceneMetrics dataclass field + return type freeze + per-stage diagnostics consumption pattern) (本 §4)
- [x] PASS criteria evaluator final (7 gates from Phase 3 §5.3 直引き + per-gate threshold rationale + tie-breaking rule + edge case handling) (本 §5)
- [x] per-stage diagnostics aggregator final (10 thresholds from Phase 3 §5.4 直引き + threshold revision pathway spec + Q5StageDiagnosticsReport finalization) (本 §6)
- [x] failure attribution methodology (per-scene F1-F12 mapping table + primary/secondary cause classification + tie-breaking rule) (本 §7)
- [x] reporting format spec (CSV schema + JSON verdict schema + summary md template + downstream consumption pattern) (本 §10)
- [x] ablation study spec (4 axis × cell count + GPU budget + minimum-viable subset + Phase 5-6 impl ablation hooks) (本 §8)
- [x] reproducibility checklist (15+ items: commit hash + dataset hash + checkpoint hash + hyperparams + env state + GPU + dependency versions + ...) (本 §11)

NEST integrity:
- [ ] state.md 12 frontmatter field 完備 (`T-Vision-CableState-Impl-Phase-4-Validation-Design/state.md` 確認)
- [ ] parent T-Vision-CableState/state.md children_nodes append + §3 update record + last_updated bump (本 leaf 完走時 確認)
- [ ] manifest §1 tree subtree + §3 status table row + §6 dependencies edges + §運用注 paragraph + last_updated bump (本 leaf 完走時 確認)
- [ ] Tier 2 deposit `_edit_requests/NNNNN-...-init.md` 起票 (sequence 採択 + collision 時 safe-adoption rename)
- [ ] memory entry + MEMORY.md index update

TOUCH FORBIDDEN compliance:
- [ ] `git diff --name-only` で改変ファイル列挙 → 全 doc-only (md / state.md / manifest / Tier 2 deposit / memory) かつ env / config / 04-Specs / types.py / vision_pipeline.py / wrist_camera_manager.py / cable_state*.py / tests/test_cable_state_*.py 全 unchanged
