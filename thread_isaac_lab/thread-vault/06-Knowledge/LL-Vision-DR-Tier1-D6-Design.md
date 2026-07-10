---
title: Vision DR — Tier 1 D6 Background Variation Design (Phase 1 spec)
node_id: T-Vision-DR-Impl-Phase1-D6-Background-Design
type: knowledge
status: prep-design (skeleton + Tier 1 spec; impl trigger pending Tier 0 PASS gate per LL-Vision-DR-Design.md §6.1)
canonical_design_source: thread-vault/06-Knowledge/LL-Vision-DR-Design.md (382 行、Rs batch approve 2026-05-03)
phase0_artifact: thread-vault/06-Knowledge/LL-Vision-DR-Impl-8DimMap.md (D1-D5 impl map、Phase 0 shipped 2026-05-04T03:25)
created: 2026-05-04T03:55:00+09:00
last_updated: 2026-05-04T03:55:00+09:00
spec_version: LL v1.0
doc_class: design-surface
---

# Vision DR — Tier 1 D6 Background Variation Design (Phase 1 spec)

This memo provides the Tier 1 prep-design artifact for D6 background variation:
the module-skeleton spec, the Tier 0→1 transition contract, the Tier 1 eval-gate
protocol, and the dataset re-render plan coordinated with T-Vision-CableState.
It complements (does not supersede) the canonical design source
`LL-Vision-DR-Design.md`; design-level rationale lives there.

The memo is the artifact that converts the Tier 1 design surface area into
impl boilerplate without re-deriving structure under impl-phase pressure
(boilerplate elimination ~2-3 h per Tier 1 impl spawn estimate, mirroring
Phase 0 boilerplate elimination for D1-D5).

---

## §0 Executive summary (~6 lines, read-must)

- **Phase 1 scope**: D6 background variation (10 preset clutter scenes via Isaac Lab `AssetBaseCfg`); Tier 1 follows Tier 0 PASS (LL-Vision-DR-Design.md §3.1 + §6.1)
- **Trigger to impl**: Tier 0 PASS gate 達成 (D1-D5 randomized eval-det SR within ±5pp + value_loss < 3× baseline + Tier 0a/b/c plateau detect 経) → Tier 1 impl spawn
- **D6 spec**: 10 preset names (`bg_empty_baseline` ~ `bg_equipment_rack`) live in `vision_dr_config.D6_BACKGROUND_PRESETS`; per-env discrete uniform sampling
- **Resource (Tier 1 only)**: ~80-100 LoC + ~3 h GPU fine-tune + ~3 h dataset re-render (T-Vision-CableState shared, coordinator-sequenced)
- **Tier 1 PASS gate**: D1-D6 randomized sim eval-det SR ≤5pp diff from Tier 0 PASS baseline (N=100 × 5 seeds, same protocol)
- **Fall-back path**: OQ-DR-2 — preset count reduction (10 → 5) if Tier 1 PASS fails on D6-D1..D5 orthogonality

---

## §1 Goal + scope

### 1.1 Goal (state.md goal_verification 経)

- **Tier 1 PASS criterion** (per LL-Vision-DR-Design.md §6.2): D1-D6 randomized sim eval-det SR が Tier 0 PASS baseline (D1-D5) と equivalence 以上 (差分 ≤ 5pp、N=100 ep × 5 seeds、cuda:2 deterministic、Tier 1 full configuration)
- **Side condition**: Tier 1 fine-tune AC value_loss < 3× Tier 0 baseline (rollback criterion per CC4 v3.2 E.6, design memo §6.1 整合)
- **Curriculum integrity**: Tier 0 PASS → Tier 1 transition は plateau detect 経 (Tier 0c から Tier 1 直接 skip 禁止、design memo §3.3)

### 1.2 Why Tier 1 separately from Tier 0 (Phase 0 D1-D5 と分離理由)

- **Curriculum stage 別**: Tier 0 ~12 h GPU sub-curriculum (0a→0b→0c) と Tier 1 ~3 h GPU stage は eval gate 別 (§6.1 vs §6.2)、impl phase 進行軸別。Phase 0 + Phase 1 を分離することで、Tier 0 PASS gate fail 時に Tier 1 spawn を skip + Tier 0 内で D8 promote 評価可能 (design memo §2.4)。
- **Asset coupling 別**: D1 (post-render scaling) / D5 (torch noise injection) は asset 不要、D2/D3 (offline pre-render dataset variants at Tier 0b) と D6 (Isaac Lab `AssetBaseCfg` USD load at Tier 1) は asset coupling pattern 別。re-render の coordinator sequencing も Tier 0b stage と Tier 1 stage で別 (§5)。
- **OQ-DR-2 path 軸**: §6.2 Tier 1 PASS fail 時の preset reduction (10 → 5) recovery、Phase 0 spec には未明文化、本 Phase 1 で明文化 (本 memo §4.3)。

### 1.3 Out-of-scope (本 Phase 1 範囲外)

- **Tier 0 D1-D5 module 改変** → Phase 0 shipped artifact 維持 (`envs/dr/{lighting,material,camera_intrinsic,sensor_noise}_variation.py` 不可触)
- **Tier 2 D7/D8** → LL-Vision-DR-Design.md §2.3 OUT-OF-SCOPE 確定 (本 leaf goal 範囲外、L1.F.1 trigger 経で別 task)
- **Curriculum class (`DRCurriculum`) impl** → 8DimMap.md §10 経で impl phase deferred (plateau-detect logic は empirical training curve で tuning 必要)。本 memo §3 は transition spec のみ提供、`DRCurriculum.step()` body は Tier 1 impl phase 担当
- **task_config.py / newton_*_env.py / 04-Specs/* 改変** → SSOT 規約 (parent state.md §4 + Phase 0 inherit + prohibited.md PhysX/Newton 規約混同禁止)
- **D6 USD asset 制作** → asset library / 既存 Isaac Lab asset registry に依存、Tier 1 impl phase で具体 USD path resolve (本 prep の preset name は abstract identifier)

---

## §2 D6 background variation spec

### 2.1 Preset list (10 presets、`vision_dr_config.D6_BACKGROUND_PRESETS`)

| Idx | Preset name | 内容 | wrist FOV 配置目安 |
|-----|-------------|------|-------------------|
| 0 | `bg_empty_baseline` | clutter なし (sim default reference) | 該当なし |
| 1 | `bg_wall_back` | 作業エリア背後の垂直壁 | y > +0.7 m (table 奥側) |
| 2 | `bg_wall_side` | 作業エリア側方の垂直壁 | x = ±0.7 m (table 横) |
| 3 | `bg_monitor_lcd` | 横置き LCD monitor | (x, y, z) ≈ (0.5, 0.4, 1.2) m |
| 4 | `bg_additional_table` | 隣接 second table | x ≈ -0.8 m (table 隣) |
| 5 | `bg_shelf_unit` | storage shelf with random objects | (x, y) ≈ (-0.5, 0.6) m, z ∈ [0.4, 1.5] m |
| 6 | `bg_cable_pile` | extra cables piled aside | table edge corner |
| 7 | `bg_paper_stack` | papers / manuals stack | table edge |
| 8 | `bg_toolbox` | closed toolbox on table edge | table edge |
| 9 | `bg_equipment_rack` | generic lab equipment rack | x ≈ -0.7 m, full vertical |

**注**: `bg_empty_baseline` を 1/10 確率で sample することで、Tier 1 train 中も clutter-free baseline scene を維持し、D6 randomization が Tier 0 baseline distribution を完全 overwrite しないよう確保する (R-DR-T1-3 mitigation)。

### 2.2 Class API (`envs/dr/background_variation.BackgroundVariation`)

| Method | Signature | 内容 |
|--------|-----------|------|
| `__init__` | `(config: VisionDRConfig, num_envs: int, device: str | torch.device)` | config 参照 + num_envs/device 保持、selection-index tensor は impl phase で allocate |
| `sample_per_env` | `(env_ids: torch.Tensor) -> None` | reset env 毎に discrete uniform で `[0, d6_background_preset_count)` から index sample |
| `load_clutter_assets` | `(env_ids: torch.Tensor) -> None` | preset name → USD path resolve、`AssetBaseCfg` instantiate |
| `apply_to_scene` | `(env_ids: torch.Tensor) -> None` | 旧 episode clutter detach + 新 clutter attach (wrist FOV 配置遵守) |

**Body**: 全 method body=NotImplementedError (本 prep は signature + docstring のみ)。Tier 1 impl phase 担当。

### 2.3 Isaac Lab AssetBaseCfg integration (verified API path)

- **Source**: `source/isaaclab/isaaclab/assets/asset_base_cfg.py:16` `class AssetBaseCfg`
- **Usage canonical**: `source/isaaclab/isaaclab/scene/interactive_scene_cfg.py:62-65` 例: `light = AssetBaseCfg(prim_path=..., spawn=..., init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, 500.0)))`
- **Tier 1 impl phase pattern**:
  ```python
  # Pseudo (impl phase only)
  for env_idx in env_ids:
      preset_name = self._config.d6_background_presets[self._sampled_idx[env_idx]]
      usd_path = DR_ASSET_REGISTRY[preset_name]  # proposed: configs/dr_assets.py
      pose = SCENE_PLACEMENT[preset_name]  # wrist-FOV-aware pose
      cfg = AssetBaseCfg(
          prim_path=f"/World/envs/env_{env_idx}/Clutter",
          spawn=UsdFileCfg(usd_path=usd_path),
          init_state=AssetBaseCfg.InitialStateCfg(pos=pose),
      )
      # attach cfg to scene at reset
  ```
- **TOUCH FORBIDDEN reminder**: D6 asset 配置 hook は newton_*_env.py 改変ではなく、明示 reset hook 経で env と非結合な adapter 経由 attach (Phase 0 + Phase 1 共通禁止事項遵守)

### 2.4 D8 promote pathway interaction (LL-Vision-DR-Design.md §2.4)

- **Pathway**: Tier 0 PASS fail + opposite-arm self-occlusion attribution dominant → D8 promote (Tier 2 → Tier 0)
- **Sequencing**: D8 promote が approved された場合、Tier 0 を D1-D5 + D8 で再 train → Tier 0 PASS gate 再評価 → Tier 1 spawn (D6 = 本 leaf scope)。D8 promote pathway は Tier 1 D6 と直交軸 (D8 は Tier 0 内で resolve、本 leaf の Tier 1 D6 spec は変更不要)。
- **Interaction risk**: D8 promote 経の Tier 0 retrain で D1-D5 baseline distribution が shift する可能性。Tier 1 PASS gate の baseline は "D8-promote-aware Tier 0 PASS baseline" として再定義 (§4.1 注記)。

---

## §3 Tier 0→1 transition spec

### 3.1 Transition trigger (DRCurriculum.step() impl-phase contract)

```
INPUT: sim_eval_det_sr_history, value_loss_history, current_tier
SOURCE: LL-Vision-DR-Design.md §3.1 (curriculum protocol) + §6.1 (Tier 0 PASS gate)

PROCEDURE:
1. IF current_tier == "0c":
     - Compute sim_eval_det_sr (Tier 0c full configuration, N=100 × 5 seeds)
     - baseline_sr = sim_eval_det_sr_no_DR (recorded at Tier 0a entry)
     - Tier 0 PASS criterion (§6.1):
         (a) abs(sim_eval_det_sr - baseline_sr) ≤ 0.05  # 5pp
         (b) value_loss_recent < 3.0 * value_loss_baseline_iter_20
         (c) Tier 0a → 0b → 0c plateau detect 経 (skip 禁止)
     - IF (a) AND (b) AND (c):
         RETURN "1"  # transition to Tier 1
     - ELIF (a) AND NOT (b):
         RETURN "ROLLBACK_TIER_0c"  # value_loss explode, fresh-start required
     - ELIF NOT (a):
         # check D8 promote trigger (§2.4)
         IF opposite_arm_occlusion_dominant():
             RETURN "TIER_0_D8_PROMOTE"
         ELSE:
             RETURN "ESCALATION_RS"  # §6.4 escalation path
2. ELIF current_tier == "1":
     - delegate to Tier 1 PASS gate (§4)
3. ELSE:
     - delegate to Tier 0a / 0b / 0c plateau detect (LL-Vision-DR-Design.md §3.2)
```

### 3.2 Activation procedure (impl-phase wiring)

When `DRCurriculum.step()` returns `"1"`:

1. `VisionDRConfig.tier` ← `"1"`
2. `VisionDRConfig.enable_d6_background` ← `True` (D1-D5 enable flags 維持)
3. `BackgroundVariation` instance を env's reset hook に register (一度のみ)
4. Dataset re-render coordinator (§5) に Tier 1 stage 開始 signal (D6 USD asset 一括 load 確認)
5. Tier 1 fine-tune ~3 h GPU 開始 (Tier 0c PASS checkpoint から resume、prohibited.md "崩壊 checkpoint resume 禁止" 該当しない — Tier 0 PASS は健全 checkpoint)

### 3.3 Reverse transition (Tier 1 → Tier 0c) 禁止

- **理由**: Tier mid 中の rollback 禁止 (LL-Vision-DR-Design.md §3.3 inherit)。Tier 1 → Tier 0c rollback = curriculum stability 破壊。
- **代替**: Tier 1 PASS fail 時は §4.3 fall-back path (OQ-DR-2 reduction) または §6.4 escalation path (Rs)。

### 3.4 Curriculum 禁止事項 (Tier 0→1 transition specific)

- **plateau detect なし transit 禁止**: Tier 0c → Tier 1 直接 skip = training collapse risk (§3.3 inherit)
- **Tier 1 fine-tune に過剰 D6 amplitude 禁止**: §2.1 preset list 拡張は Wide DR slip risk (§3.3 inherit)
- **D6 enable + Tier 0c flag disable 禁止**: §3.2 #2 で D1-D5 enable 維持 (Tier 1 = D1-D6、D1-D5 削除は curriculum integrity 破壊)

---

## §4 Tier 1 eval gate spec

### 4.1 PASS criterion (LL-Vision-DR-Design.md §6.2 verbatim + Phase 1 protocol detail)

**Criterion**:
- D1-D6 randomized sim eval-det SR (N=100 ep × 5 seeds、cuda:2 deterministic、Tier 1 full configuration: `enable_d1..d6 = True`、Tier 1 fine-tune checkpoint) が **Tier 0 PASS baseline** (D1-D5 randomized SR、§6.1 で記録) と equivalence 以上 (差分 ≤ 5pp、within ±5pp interval)
- **D8 promote interaction (§2.4 注記)**: D8 promote pathway 採択時の Tier 0 baseline は "D8-promote-aware Tier 0 PASS baseline" (D1-D5+D8 randomized SR) として再定義、本 §4.1 PASS criterion の baseline は そちら参照
- Tier 1 fine-tune 中の AC value_loss が Tier 0 baseline value_loss の 3× 未満 (CC4 v3.2 E.6 rollback criterion 整合、§3.1 #1(b) と同 threshold)

### 4.2 Eval protocol (verbatim with Tier 0 protocol、reproducibility 確保)

| Step | Protocol |
|------|----------|
| Eval mode | sim eval-det (deterministic policy rollout、no exploration noise) |
| Episode count | N=100 ep per seed |
| Seed count | 5 seeds (independent draws) |
| Device | cuda:2 (Newton VBD env) |
| Randomization config | Tier 1 full: `enable_d1..d6 = True`, all preset sets at default `vision_dr_config.D6_BACKGROUND_PRESETS[:d6_background_preset_count]` |
| Baseline config | Tier 0 PASS baseline (D1-D5 randomized SR、§6.1 記録時点) |
| Aggregation | mean SR across (N × seeds) episodes、95% CI Wilson interval |
| PASS judgement | abs(Tier 1 mean SR - Tier 0 PASS mean SR) ≤ 0.05 (5pp absolute) |

**注**: Tier 0 PASS baseline は §6.1 evaluation 時に必ず persistent storage (`results/tier0_pass_baseline.json` 等) に記録、Tier 1 PASS gate evaluation 時に reference 必須。同一 baseline 比較で curriculum integrity 確保。

### 4.3 Fail handling (OQ-DR-2 fall-back path 明文化)

| Fail mode | 判定基準 | Action |
|-----------|---------|--------|
| **F1: 差分 > 5pp + value_loss < 3× baseline** | Tier 1 D6 randomization が D1-D5 と orthogonal でない (semantic seg confusion 等) | OQ-DR-2 reduction: `d6_background_preset_count` 10 → 5 (上位 5 preset only: `bg_empty_baseline`, `bg_wall_back`, `bg_wall_side`, `bg_monitor_lcd`, `bg_additional_table`)。Tier 1 fine-tune 再 run。再評価 |
| **F2: value_loss > 3× baseline** | AC fine-tune collapse (D6 添加で value function instability) | fresh-start with Tier 0 PASS ckpt + OQ-DR-2 (preset 5)。prohibited.md "崩壊 checkpoint resume 禁止" 遵守 (collapse ckpt resume せず、Tier 0 PASS ckpt から再開) |
| **F3: F1 + F2 両方** | Tier 1 D6 設計 root cause | §6.4 escalation path (Rs) — preset selection 再 design / wrist FOV 配置 root cause 検証 |
| **F4: F1 + OQ-DR-2 reduction でも fail** | preset reduction で improve せず、D6 自体の sim-domain mismatch | §6.4 escalation path (Rs) — D6 dim 自体の Tier 1 inclusion 再評価 (Tier 2 retire candidate) |

### 4.4 Eval gate execution timing

- **Tier 1 fine-tune 中**: ~500k iter 毎に periodic eval (early failure detection)
- **Tier 1 fine-tune 終了時**: 最終 eval gate evaluation (§4.1 PASS criterion 適用)
- **失敗時の rollback**: F2 該当時即時 fresh-start、F1 該当時 fine-tune 完了後 OQ-DR-2 適用

---

## §5 T-Vision-CableState shared dataset re-render plan

### 5.1 Re-render scope (Tier 1 stage、~3 h GPU)

| Asset | Count | Per-asset render cost | Total |
|-------|-------|----------------------|-------|
| D6 background USD assets × scene variants | 10 preset × 500 scene-variant rolls | ~ 0.5 sec/render | ~42 min |
| Cable + clip cross-render with each background | 5k samples × 10 background = 50k effective | ~ batch effects | ~2 h |
| Verification render (sanity check 100 samples per preset) | 1k samples | minimal | ~10 min |
| Buffer (re-render retry / asset path resolve issue) | — | — | ~10 min |
| **Total** | — | — | **~3 h GPU** |

### 5.2 Coordinator sequencing (T-Vision-CableState shared)

- **Pre-condition (本 Phase 1 prep の責任範囲外、Tier 1 impl phase 担当)**:
  - T-Vision-CableState Phase 2 (Stage C DD-PINN warm start、~25 h GPU + 5k labeled dataset) IN_PROGRESS / COMPLETE
  - T-Vision-DR Tier 0 PASS gate 達成 (§6.1)
- **Re-render execution sequence**:
  1. T-Vision-CableState coordinator 経で Tier 1 stage re-render slot を割当 (T-Vision-CableState Phase 2 の DD-PINN 訓練 dataset re-render と asset path 共有確認)
  2. D6 USD asset 一括 load (~42 min)
  3. Cable + clip cross-render with each background (~2 h、batch parallelize)
  4. Verification render (~10 min)
  5. Asset path 共有 storage に commit: `data/dr_dataset_v1/tier1_d6/{preset_name}/` (`.gitignore` "data/" 配下、Phase 0 spec §5.2 と同 root)
- **Coordinator responsibility split**:
  - T-Vision-CableState side: dataset shape (5k samples) + label generation + Phase 2 DD-PINN training trigger
  - T-Vision-DR side (本 prep): D6 background asset list + per-preset scene placement + verification render protocol

### 5.3 Asset path resolution (Tier 1 impl phase 担当)

- **Proposed module**: `thread_isaac_lab/configs/dr_assets.py` (新 module、Tier 1 impl phase で起票)
- **Content**: dict mapping `D6_BACKGROUND_PRESETS` entries → Isaac Lab USD asset path (e.g., `omniverse://...` or local asset path)
- **Resolution timing**: `BackgroundVariation.load_clutter_assets()` impl phase で参照
- **Asset library source candidates**: Isaac Lab built-in asset library (`omni.isaac.lab_assets`) / custom THREAD asset directory (`thread_isaac_lab/data/dr_assets/`、`.gitignore` "data/" 配下)

### 5.4 Re-render 禁止事項

- **T-Vision-CableState Phase 2 進行中の slot 横取り禁止**: coordinator queue 経で sequence、Phase 2 DD-PINN training を中断しない
- **既存 Tier 0b dataset (D2 + D3) との混合禁止**: Tier 1 d6 dataset は別 directory (`tier1_d6/`)、Tier 0b dataset (`tier0b_d2d3/`) と path 分離 (asset bleed 防止)
- **gitignore 違反禁止**: dataset は全て `data/` 配下、git commit 不可 (asset volume 大、Phase 0 spec §5.2 inherit)

---

## §6 Risk register (Tier 1-specific)

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R-DR-T1-1** | Wrist FOV 配置 mismatch: D6 asset を wrist 視野外に配置 → randomization 効果 0、Tier 1 PASS gate fail (false negative) | **HIGH** | §2.1 配置目安 table 経で各 preset の wrist FOV 内 placement 明文化、impl phase で per-preset pose を `SCENE_PLACEMENT` dict に register、verification render (§5.1 step 3) で wrist 視点画像を sampling 確認 |
| **R-DR-T1-2** | D6 と D1-D5 の orthogonality 破壊: D6 background 添加で D1-D5 randomization signal を mask → Tier 0 PASS baseline distribution が Tier 1 で崩れ、equivalence ≤5pp 評価が baseline shift で過剰評価 | HIGH | §4.1 注記の "Tier 0 PASS baseline reference" persistent storage 必須、Tier 1 評価時に同一 baseline 比較確保。F1 fail 時 OQ-DR-2 reduction 経で改善見込み (§4.3) |
| **R-DR-T1-3** | clutter-only distribution shift: 全 episode で clutter ありになると "clutter-aware" overfit 発生、Tier 0 baseline (clutter-free) との equivalence 評価で偏向 | MEDIUM | §2.1 注で `bg_empty_baseline` を 1/10 確率で sample (baseline scene 維持)、clutter-free episode を 10% 比率で確保 |
| **R-DR-T1-4** | Asset path resolve failure: Isaac Lab asset library に preset 該当 USD 不在 / custom asset 未制作 | MEDIUM | Tier 1 impl phase 担当、本 prep では preset name は abstract identifier、impl phase で `dr_assets.py` を起票時に asset library inventory 確認、不在時は §6.4 escalation path (asset 制作 task 起票候補) |
| **R-DR-T1-5** | Dataset re-render slot 競合: T-Vision-CableState Phase 2 DD-PINN training (~25 h GPU) と Tier 1 D6 re-render (~3 h GPU) が GPU 共有で competition | MEDIUM | §5.2 coordinator queue 経で sequence (Phase 2 完了後 Tier 1 re-render slot 割当)、または Phase 2 dataset re-render と D6 re-render を 1 回 batch で実行 (asset path 共有確認後) |
| **R-DR-T1-6** | OQ-DR-2 reduction (10 → 5) 後も Tier 1 PASS fail: D6 dim 自体が sim-domain で Tier 1 inclusion 不適 | MEDIUM | §4.3 F4 経で escalation path、D6 を Tier 2 retire candidate として再評価 (Rs decision 必須、本 leaf scope 拡張 vs Tier 1 inclusion 取下げの判断) |
| **R-DR-T1-7** | D8 promote pathway interaction: D8 promote (Tier 2 → Tier 0) 経の Tier 0 retrain で baseline distribution shift、Tier 1 PASS gate baseline が "D8-promote-aware" に変化 | LOW | §4.1 注記で baseline reference を "D8-promote-aware Tier 0 PASS baseline" として再定義、§2.4 interaction 明文化 |
| **R-DR-T1-8** | TOUCH FORBIDDEN 違反 risk: D6 impl phase で newton_*_env.py 改変 / task_config.py 変更が誘発 | LOW | §2.3 impl pattern で明示 reset hook adapter 経由 attach、parent state.md §4 + Phase 0 inherit + 本 memo §1.3 で禁止事項明文化 |

---

## §7 Cross-references

### 7.1 Parent / sibling NEST nodes

- **Parent (本 leaf)**: `thread-vault/T-Vision-DR-Impl-Phase1-D6-Background-Design/state.md` (本 Phase 1 NEST node、IN_PROGRESS 2026-05-04T03:50)
- **Grand-parent**: `thread-vault/T-Vision-DR/state.md` (L1.A.3 leaf、APPROVED design phase 2026-05-03)
- **Sibling precedent**: `thread-vault/T-Vision-DR-Impl-Phase0-PrepDesign/state.md` (Phase 0、D1-D5 skeleton + 8DimMap shipped 2026-05-04T03:25)
- **Shared dataset coordinator**: `thread-vault/T-Vision-CableState/state.md` (Phase 1 COMPLETE 2026-05-04T03:35、Phase 2 DD-PINN pending)
- **Downstream consumer**: `thread-vault/T-Vision-Fusion/state.md` (Late Fusion 50D obs、Tier 1 D6 fine-tune 後の policy obs に反映)

### 7.2 Canonical design source + Phase 0 artifact

- **Canonical design source**: `thread-vault/06-Knowledge/LL-Vision-DR-Design.md` (382 行、Rs batch approve 2026-05-03、§2.2 D6 + §3.1 Tier 0→1 transition + §6.2 Tier 1 eval gate)
- **Phase 0 8DimMap**: `thread-vault/06-Knowledge/LL-Vision-DR-Impl-8DimMap.md` (D1-D5 entry-point map + §7 D6 deferred map → 本 Phase 1 で skeleton present 反映)

### 7.3 Code references (Phase 1 prep deliverable + impl phase target)

- **Phase 1 prep deliverable (本 memo coordinated)**:
  - `thread_isaac_lab/envs/dr/background_variation.py` (D6 skeleton、本 Phase 1 で起票)
  - `thread_isaac_lab/configs/vision_dr_config.py` D6 拡張 (`D6_BACKGROUND_PRESETS` + `d6_background_presets` field、本 Phase 1 で追加)
  - `thread_isaac_lab/envs/dr/__init__.py` BackgroundVariation export (本 Phase 1 で更新)
- **Tier 1 impl phase target (本 prep 範囲外)**:
  - `thread_isaac_lab/configs/dr_assets.py` (新 module、preset name → USD path registry)
  - `thread_isaac_lab/envs/dr/curriculum.py` (`DRCurriculum.step()` body、Tier 0→1 transition logic 含む)
  - Newton env reset hook (具体 file は impl spawn で確定、TOUCH FORBIDDEN bypass の明示 hook only)
- **Isaac Lab AssetBaseCfg API**:
  - `source/isaaclab/isaaclab/assets/asset_base_cfg.py:16` `class AssetBaseCfg`
  - `source/isaaclab/isaaclab/scene/interactive_scene_cfg.py:62-65` (canonical usage example)

### 7.4 04-Specs reference (read-only)

- **04-Specs Vision Pipeline.md** (R6 Stage 1-4 spec、本 design は Stage 1-2 robust 化に位置付け、Stage 3 physics model と直交、D6 background は Stage 1 mask robustness の Tier 1 stress test)
- **04-Specs Camera Backend.md** (Phase 2 RGB+depth pipeline、本 design extension の base、wrist camera FOV constraint 参照)
- **04-Specs SOMA.md** (L0 / L1 / L2 goal、本 leaf goal は L0 vision-based 95% への precursor)
- **06-Knowledge LL-VisualObs-CameraSystem.md** (camera spec、`wrist_camera_manager.py` design rationale、wrist FOV constraint 参照)
- **06-Knowledge LL-Newton.md** (Newton 環境制約、Isaac Lab AssetBaseCfg と Newton scene-graph 統合の reference)

### 7.5 Path Y / discipline references

- `feedback_premise_change_impact_analysis.md`: §2.4 D8 promote pathway interaction を Tier 1 D6 spec に proactive impact analysis で fold-in
- `feedback_check_existing_eval_grep.md`: §2.3 で `AssetBaseCfg` actual API source (asset_base_cfg.py:16 + interactive_scene_cfg.py:62-65) 経で fact-finding
- `feedback_factual_api_verification.md`: §2.3 で Isaac Lab AssetBaseCfg API path 照合 (verified at source/isaaclab/isaaclab/assets/asset_base_cfg.py:16)
- `feedback_geometric_vs_empirical_bc.md`: §4.1 / §4.3 で empirical eval gate (Tier 1 PASS = sim eval-det SR equivalence) を geometric/diagnostic 単独 NO-GO に依存させない
- `feedback_recommendation_policy_2026-04-30.md`: §0 で Tier 1 D6 spec を Phase 0 prescribed structure の continuation として位置付け、本 memo は selection result の Phase 1 detail (新規推奨でなく Phase 0 + canonical design memo の structured continuation)

---

**Status**: Phase 1 prep design active, Tier 1 impl pending Tier 0 PASS gate (LL-Vision-DR-Design.md §6.1) + Rs §3.1 #4 起動承認
**Owner**: T-Vision-DR-Impl-Phase1-D6-Background-Design-CC (本 session、prep design phase only)
**Next trigger**: Tier 0 PASS gate 達成 → Rs §3.1 #4 起動承認経で `CC-L1A-Vision-DR-Tier1-Impl` 起票
