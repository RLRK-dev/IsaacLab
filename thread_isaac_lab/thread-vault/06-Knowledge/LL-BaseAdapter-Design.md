---
title: LL-BaseAdapter-Design
created: '2026-04-04T14:55:19.045Z'
tags:
  - knowledge
  - rl
  - adapter
  - base-model
  - architecture
doc_class: design-surface
---

# Base Policy vs Skill Adapter 設計知見

> Created: 2026-04-04 (Session 90)
> Context: 3スキル adapter訓練 (AC v33 / IC v13 / AR v19) 起動後の設計分析

---

## アーキテクチャ概要

```
[Base backbone: 42→128→128 (frozen)] → latent 128D
[Base head: 128→12 (frozen)]          → base_action 12D
[Adapter: LoRA+MLP+gate (trainable)]  → adjustment 12D
final_action = base_action + adjustment   ← 残差接続
```

- Base: 23,564 params (frozen)
- Adapter: 3,997 params (LoRA rank=8 + MLP 144→16→12 + gate)
- Trainable total: 26,154 (adapter + critic + std)
- 実装: `thread_isaac_lab/models/skill_adapter.py`

## Base Modelの2つの役割

**A) Action品質 (base_action の正確さ):**
- 残差接続のため、base_actionが正確なほどadapter adjustmentは小さくて済む
- ただしbaseはskill条件なしの混合モデル → 原理的に各スキル最適解は出せない
- base v2 per-skill BC loss: GC=0.0016, IC=0.0019, AR=0.0549
- GC/ICは十分低い。ARが高いのはdemo分布の特性（ease_distなど追加要素）

**B) Feature品質 (128D latentの情報量):**
- adapterはlatent + skill_embedding(16D) からadjustmentを計算
- latentが「ハンド-ケーブル相対位置」「向きずれ」をエンコードしていれば修正方向を学べる
- **これがbaseの本質的な役割**
- 3スキル混合BCでobs空間のカバレッジは広い → feature品質は悪くないはず

## 実測データ (2026-04-04)

### Base v2 BC Loss (per-skill)

| Skill | Base v2 BC Loss | 旧base BC Loss | 改善 |
|-------|----------------|----------------|------|
| GC | 0.0016 | — | — |
| IC | 0.0019 | 0.0073 | 3.8x |
| AR | 0.0549 | — | — |

### Adapter DAPG bc_loss (初期)

| Skill | Adapter bc_loss @初期 | Base BC loss | 比 |
|-------|----------------------|-------------|-----|
| AC v33 | 2.27 (@iter0) | 0.0016 | 1419x |
| IC v13 | — | 0.0019 | — |
| AR v19 | 0.083 (@iter0) | 0.0549 | 1.5x |

**GC adapter bc_loss が base BC loss の1419倍高い理由:**
1. DAPG初期α=0.3でexploration noiseが乗る（standaloneでも同等）
2. adapter zero-init → adjustment≈0 の状態でRLのaction noiseが加算
3. env obs分布 ≠ demo obs分布（exploration由来のshift）

**AR adapter bc_loss が異常に低い理由:**
- AR demo分布がbase latent空間上でコンパクト
- または AR obs領域がGC/ICと重複少なく、干渉なし
- → ARが最初に収束する可能性高い

## 判断基準 (完走後)

| adapter結果 | 診断 | 対策 |
|------------|------|------|
| adapter ≈ standalone | base十分。Phase 5統合へ | なし |
| adapter >> standalone | adapter容量不足 | lora_rank: 8→16, MLP拡張 |
| rank上げても改善なし | base feature不足 | backbone上層unfreeze or skill-conditioned base |
| ARのみ良好、GC/IC停滞 | スキル別demo品質/量の差 | demo改善（GC warmupの分散、IC成功率11%） |

## 比較ベースライン (standalone DAPG, adapter不使用)

| Skill | Version | dist_pos | dist_ori | 備考 |
|-------|---------|----------|----------|------|
| GC | v32 | 3.2mm | 3.1° | 200/200 |
| AR | v18 | 13.0mm | 5.3° | 200/200 |
| IC | v12 adapter (旧base) | 19.3mm | — | 200/200 |

## Related

- [[RL-Routing-Design]] §5 (Skill Adapter統合)
- [[RL-Routing-Progress]] (訓練進捗)
- [[LL-ApproachCable-BugHistory]] (bc_loss関連バグ経緯)
