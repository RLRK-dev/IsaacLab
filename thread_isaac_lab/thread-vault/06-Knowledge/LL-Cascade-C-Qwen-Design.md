---
title: LL-Cascade-C-Qwen-Design
created: '2026-04-27'
superseded_at: '2026-04-29T02:40:00+09:00'
superseded_by: LL-Cascade-C-Nemotron-Design (ACTIVE 2026-05-03、640 lines / 48KB、Rs delegation 経 sub-agent dispatch で起票完了)
supersession_reason: Rs γ disposition 経 model choice authority 行使 (NVIDIA hardware native optimization + ecosystem 統合 を Qwen size/latency 利点に勝負させ採用)
tags:
  - knowledge
  - world-model
  - cascade
  - llm-orchestrator
  - qwen
  - superseded
status: superseded
related:
  - LL-WorldModel-Feasibility
  - LL-Orchestration-Design
  - LL-Cosmos
  - FSM-LLM-Recovery
  - LL-Cascade-C-Nemotron-Design (active successor)
doc_class: design-surface
---

> ## ⚠️ SUPERSEDED 2026-04-29
>
> 本 design memo は **Rs γ disposition (2026-04-29 L0-Coordinator#s4 chat)** 経で model 選択 Qwen2.5-0.5B → **Nemotron Mini 4B + TensorRT-LLM** に切替.
>
> - **Active successor**: `LL-Cascade-C-Nemotron-Design.md` (**ACTIVE 2026-05-03**、640 lines / 48KB / §0-§10、Rs delegation 経 sub-agent dispatch で起票完了、precedent: Main CC B sub-agent 3 が本 Qwen design 担当)
> - **本 memo の保持理由**: design rationale + impl roadmap 比較 baseline、historical reference (γ-1 minimal update path で archive せず in-place supersedence note)
> - **Re-evaluation cause**: 7-CC Debate (2026-04-25) では Nemotron が KNOWN_ALTERNATIVES に上がらず、本 design は Qwen 前提で start. Rs explicit query (2026-04-29) で Nemotron 利点 (TensorRT-LLM 2-3x speedup + Triton 統合 + Reward model 将来 reuse) が surface、design memo gap として γ disposition 採択.
> - **Model-independent components**: dataset prep (A0)、Gate 2 PASS condition (accuracy ≥ 0.60)、orchestrator hook injection point (`execute_step` L1002-1075 pre-attempt hook ~30-50 LoC)、JSON verdict schema は Nemotron design でも reuse 可能.
> - **Model-dependent components (re-design 必要)**: model size/latency budget (Qwen 0.5B 1GB 22ms → Nemotron 4B 8GB ~30-50ms TensorRT compiled)、fine-tune toolchain (Qwen LoRA HuggingFace → Nemotron NeMo framework)、VLM Tier-2 候補 (Qwen2.5-VL-7B production mature → NVLM research-tier risk noted).
>
> **以降の design 内容 = Qwen 前提、Nemotron 切替後は historical reference のみ参照**.

---

# LL-Cascade-C-Qwen-Design (SUPERSEDED 2026-04-29)

WM Cascade C (Qwen2.5-VL 60% integration) architecture design knowledge entry.

Cascade A→C→{B|D} sequence の Cascade C の formal spec。Cluster G floor (`routing_orchestrator.py` 1271 LoC、shipped) の **upstream extension** として Qwen2.5 fault classifier + recovery proposer を加え、WM Gate 2 unlock 条件を達成する design。

## 関連 Vault docs

- 上流: [[LL-WorldModel-Feasibility]] §7 (LLM-Orchestrator impl spec) + §8 (Cascade plan + Gates 1-4)
- sister: [[LL-Orchestration-Design]] (existing orchestrator architecture)、[[LL-Cosmos]] (Cascade B 候補、本 design は scope 外)、[[FSM-LLM-Recovery]] (historical context)
- 7-CC Debate verdict: memory/`project_wm_debate_7cc_complete_2026-04-25.md`

## Project memo (canonical source)

完全な design memo は `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_l1e_cascade_c_qwen_design_complete_2026-04-27.md` を参照。本 vault entry は要約 + cross-ref。

## 推奨 architecture (one-line summary)

- **model**: Qwen2.5-0.5B (proprio-only fault classifier、22 ms latency) + Qwen2.5-VL-7B-Instruct (vision-aware recovery proposer、CC#5 統合後 activate) の **2-tier hybrid**
- **trigger**: Hybrid (Tier-1 RUN_METRICS post-skill + Tier-2 vision-based mid-episode)、Cluster G の terminal classification を補強する non-terminal early-warning channel
- **recovery action mapping**: Structured JSON (skill choice + retry_seed + scripted_fallback flag)、orchestrator 側 dispatcher で展開、LLM untyped action 直出力は禁止
- **Gate 2 measurement**: synthetic failure injection (5 mode × 4 skill = 20 bucket、~400 sample) + real failure detection (G5 wet-run logs)、aggregated accuracy ≥ 60% (BiCICLe Straighten Rope 34.3% を low bar)
- **impl roadmap**: A0 dataset prep ~5h → A1 0.5B fine-tune ~10h → A2 orchestrator hook ~8h → A3 Gate 2 bench ~10h → A4 7B VL spike ~10h (conditional) = total **~33-43h CC + ~13-23h GPU**

## Cluster G floor unchanged

env / scripted_skills / step_table file UNCHANGED 制約遵守。Cascade C は existing `RoutingOrchestrator.execute_step` L1050 attempt loop の **pre-attempt hook** として injection、Cluster G の retry/rollback engine 自体は不変。

| Cluster G component | Cascade C 影響 |
|---------------------|----------------|
| `RoutingOrchestrator.execute_skill` L862-899 | 不変 |
| `RoutingOrchestrator.execute_step` L1002-1075 | pre-attempt hook 追加のみ (~30-50 LoC) |
| `RoutingOrchestrator._rollback` L1103-1153 | bc_p0_region_check 拡張 (~10 LoC) |
| `_PerArmClampTracker` / derive_clamp_r_skill_result | 不変 |
| Snapshot cascade | 不変 |
| `derive_skill_result` L372-422 | 不変 |
| `SkillResult` enum (skills/result.py) | 不変 (Cascade C は SkillResult 上に layer) |

## Gate 2 official 定義

> **Gate 2**: Qwen2.5-0.5B fine-tuned cable fault classifier の **failure detection accuracy ≥ 60%** (proprio + log_per_world feature only、CC#5 vision integration 前 baseline)、aggregated accuracy = 0.7 × synthetic + 0.3 × real。

PASS で Cascade C 本番化 → Gate 3 (OOD coverage) 評価へ進む。

PARTIAL (synthetic > 60% but real < 40%) で Tier-2 vision proposer (Phase 2) 必要。

FAIL で Option D freeze (Phase 5-3 集中)。

## 別 task 起票候補 (CC dispatch)

1. **CC-L1E-Cascade-C-Qwen-Impl-A0** — dataset prep (~150 LoC、Phase 5-2 G5 wet-run COMPLETE 待ち)
2. **CC-L1E-Cascade-C-Qwen-Impl-A1** — classifier fine-tune (~200 LoC、A0 完了 + GPU resource)
3. **CC-L1E-Failure-Detection-Bench-A3** — Gate 2 measurement (~150-200 LoC、A1 + A2 完了)

(A2 orchestrator hook + A4 VLM spike は A1 結果 / CC#5 progress 次第で起票)

## 接続箇所詳細 (orchestrator hook spec)

```python
# pseudo-code、impl は CC-L1E-Cascade-C-Qwen-Impl-A2 で本実装
class LLMFaultClassifier:
    """Tier-1 + Tier-2 hybrid Cascade C classifier."""

    def __init__(self, classifier_ckpt: Path, vlm_ckpt: Path | None = None):
        self.tier1 = load_qwen_05b_lora(classifier_ckpt)  # 22 ms
        self.tier2 = load_qwen_vl_7b(vlm_ckpt) if vlm_ckpt else None  # 150-200 ms, optional

    def classify(self, obs: dict, image: torch.Tensor | None = None) -> dict:
        """Return verdict JSON per sub-task 3.1 schema."""
        v1 = self.tier1.infer(obs)
        if v1["confidence"] >= 0.85 or self.tier2 is None:
            return v1
        # Tier-2 fallback
        return self.tier2.infer(obs, image)


def cascade_c_dispatch(verdict: dict, default_step_id: int) -> tuple:
    """Map LLM JSON verdict to (skill_override, retry_seed, scripted_fallback).

    Returns:
        (skill_override: SkillName | None, retry_seed: int | None, scripted_fallback: bool)
    """
    if verdict["verdict"] == "OK" or verdict["confidence"] < 0.85:
        return (None, None, False)
    rec = verdict["recommended_action"]
    skill_override = SkillName[rec["skill_override"]] if rec["skill_override"] else None
    return (skill_override, rec["retry_seed_override"], rec["scripted_fallback"])


# RoutingOrchestrator.execute_step modification (~30-50 LoC):
#   for attempt in range(self.MAX_RETRY + 1):
#       if attempt > 0 and self.cascade_c is not None:  # NEW
#           obs, _ = self.env.get_observations()
#           verdict = self.cascade_c.classify(obs)
#           skill_override, retry_seed_override, _ = cascade_c_dispatch(verdict, step_id)
#           if retry_seed_override is not None:
#               base_seed = retry_seed_override  # override C7 default
#       if attempt > 0:
#           torch.manual_seed(base_seed * 1000 + attempt)
#       result = self.execute_skill(step_id, max_rl_steps=max_rl_steps)
#       ...  # existing Cluster G path
```

## CC dispatch 用 Goal / Purpose / Role template

新 task 起票時の launch instruction template (本 design を踏襲):

- **Goal**: <CC-L1E-Cascade-C-Qwen-Impl-A0 の場合> dataset fixture (synthetic 5 mode × 4 skill + real failure log harvest) 構築完了、A1 fine-tune 入力可能 state
- **Purpose**: WM Cascade C Tier-1 classifier (Qwen2.5-0.5B) fine-tune 前提、Gate 2 measurement bench (A3) 入力 dataset prep。本 design memo `LL-Cascade-C-Qwen-Design` の roadmap 1/3
- **Role**: A0 dataset prep 専任、A1/A2/A3 は別 task

## Caveats

- Tier-2 VL-7B (Phase 2 deferred) は CC#5 MVP-2B 完成後 activate
- Track 2 real failure detection は Phase 5-2 G5 wet-run + Phase 5-3 短期 milestone empirical logs 必要 (現状 G5 blocked)
- LoRA fine-tune hyperparameter は A1 phase で empirical 確定
- Cluster G LoC 1271 は 2026-04-27 snapshot (source memo 877 は 2026-04-25 historical)

---

**Created:** 2026-04-27
**Status:** 🟢 Active design (impl 待ち、CC-L1E-Cascade-C-Qwen-Impl-A0/A1/A3 別 task 起票後)
