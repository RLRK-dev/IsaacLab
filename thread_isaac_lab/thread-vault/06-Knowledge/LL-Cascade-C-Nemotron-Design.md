---
title: LL-Cascade-C-Nemotron-Design
created: '2026-05-03'
status: approved (Rs batch approve 2026-05-03 T-ROOT-COORD#s11) + ready_for_impl_spawn (impl trigger pending dependency: G5 wet-run COMPLETE / NeMo container deploy / GPU resource 確保 / CC-T-WM-G2-A0 dataset prep 起票指示)
finalized_at: '2026-05-03T12:13:00+09:00'
supersedes: LL-Cascade-C-Qwen-Design (2026-04-29 Rs γ disposition)
authority_source: Rs γ disposition (2026-04-29 L0-Coordinator#s4 chat) + Rs delegation (2026-05-03 design finalize)
deferred_to_impl_spawn:
  - task_spawn_order (A0→A1→A3→A2 vs A0→A1→A2→A3): 各 task 内で再評価
  - latency_PARTIAL_fallback (async polling / Qwen0.5B rollback): A3 phase で empirical 経 disposition
  - nemo_install_isolation (env_isaaclab6 conflict risk、別 container 候補): A1 phase 着手前 separate sub-task で確認
  - tier2_vl_reeval_trigger (Qwen2.5-VL-7B vs NVLM): Phase 2 起動条件 (CC#5 MVP-2B 完成 + Gate 2 PASS) 該当時 再判定
tags:
  - knowledge
  - world-model
  - cascade
  - llm-orchestrator
  - nemotron
  - tensorrt-llm
related:
  - LL-WorldModel-Feasibility
  - LL-Orchestration-Design
  - LL-Cascade-C-Qwen-Design (superseded predecessor)
  - LL-Cosmos
  - FSM-LLM-Recovery
doc_class: design-surface
---

# LL-Cascade-C-Nemotron-Design

WM Cascade C (Nemotron Mini 4B + TensorRT-LLM fault classifier) architecture design knowledge entry。
Cascade A→C→{B|D} sequence の Cascade C **active design**、`LL-Cascade-C-Qwen-Design.md` を 2026-04-29 Rs γ disposition で supersede。Cluster G floor (`routing_orchestrator.py` 1271 LoC、shipped) の **upstream extension** として Nemotron Mini 4B fault classifier + recovery proposer を加え、WM Gate 2 unlock 条件 (accuracy ≥ 0.60 aggregated + TensorRT-LLM compiled latency ≤ 100ms) を達成する design。

---

## §0 Active design + supersession context

本 memo は **Cascade C active design**、Qwen2.5-0.5B 前提の `LL-Cascade-C-Qwen-Design.md` (2026-04-27) を Rs γ disposition (2026-04-29 L0-Coordinator#s4 chat) で supersede した successor。Qwen design は historical reference として in-place supersedence note 維持 (γ-1 minimal update path、archive せず)、cross-ref を保持。

### Why Nemotron + TensorRT-LLM (Rs γ rationale 4 reasons)

1. **NVIDIA hardware native optimization**: TensorRT-LLM compiled engine による HuggingFace transformers 直接 inference 比 2-3x speedup 期待 (estimated, no direct source、TensorRT-LLM official docs blocked from this env)。RTX A6000 + RTX PRO 4000 Blackwell の native CUDA arch 最適化が hardware ROI を 最大化
2. **NVIDIA ecosystem 統合**: Triton Inference Server backend + NeMo framework fine-tune + NGC catalog の official model serving が単一 vendor stack で完結。THREAD project は既に Isaac Sim / Newton / Isaac Lab を NVIDIA stack で構築済、Qwen のような third-party model 前提より operational consistency が高い
3. **Reward model variant 将来 reuse 可能性**: Nemotron Mini 4B は base + instruct + reward variant 系列で展開予定 (NVIDIA model family pattern)。THREAD の WM Cascade B (Cosmos) / Foundational WM (Cascade D) で reward model 必要時、同一 base model を reuse 可能 (Qwen ecosystem は reward model 系列が薄い)
4. **On-device inference 最適化済み**: Nemotron Mini 4B official 設計目標 = on-device deployment (verified: HuggingFace model card "On-device deployment optimized for speed" intended use case)、edge GPU (RTX PRO 4000 Blackwell 24GB tier) で実用 latency が達成しやすい

### Trade-offs accepted (Rs γ explicit、design memo に明記)

| Axis | Qwen2.5-0.5B baseline | Nemotron Mini 4B + TensorRT-LLM | 容認した trade-off |
|------|------------------------|-----------------------------------|---------------------|
| Model size | ~1.0 GB FP16 / ~0.5 GB INT4 | ~8 GB FP16 / ~2 GB INT4 (estimated) | +7x size、cuda:2 PRO 4000 24GB の ~6 GB free 制約に impact (INT4 必須) |
| Latency (per inference) | 22 ms (NVIDIA Jetson 検証済、Qwen design Step 7) | ~30-50 ms TensorRT compiled (estimated, no direct source) | +1.4-2.3x latency、ただし Gate 2 budget 100ms 内 |
| Compilation overhead | None (HuggingFace native) | ~1-2 hours one-time `trtllm-build` (estimated) | one-time cost、runtime budget には含めない |
| Toolchain complexity | HuggingFace + PEFT (light) | NeMo framework + TensorRT-LLM build (heavy) | install/setup の +5-8 hours engineering overhead |
| Maturity (THREAD specific) | Qwen design memo + 7-CC Pre-Debate verdict | 新規 stack、CC 未経験 | impl A1 phase で baseline validation 必要 |

### Inheritance map (Qwen design からの継承 vs 再設計)

**Inheritance — model-independent components (Qwen design memo §-cite で reuse、本 memo では duplicate せず)**:
- A0 dataset prep: 5 mode × 4 skill = 20 buckets × ~80 samples = ~400 synthetic + real failure log harvest (Qwen design §4.2 Track 1/Track 2)
- JSON verdict schema: `{verdict, confidence, failure_mode, recommended_action: {skill_override, retry_seed_override, scripted_fallback, rollback_depth_hint}, reasoning}` (Qwen design §3.1 (b))
- Orchestrator hook injection point: `RoutingOrchestrator.execute_step` L1050 attempt loop pre-attempt hook、~30-50 LoC (Qwen design §2.3 + §3.3)
- Gate 2 PASS formula: aggregated accuracy = 0.7 × synthetic + 0.3 × real ≥ 0.60 (Qwen design §4.3)
- F1-F7 failure mode taxonomy: F1 explosion / F2 cable drop / F3 timeout / F4 partial success / F5 OOD / F6 cable slack / F7 finger fail (Qwen design §2.1)
- Cluster G floor unchanged 制約: env / scripted_skills / step_table file UNCHANGED、orchestrator side のみ injection (Qwen design §5.3)

**Re-design — model-dependent components (本 memo §1-§9 で詳細、Qwen design では未対応)**:
- Model size / VRAM allocation 再計画 (Qwen 1GB → Nemotron 4B 8GB FP16、INT4 必須化検討)
- Latency budget breakdown (Qwen 22ms → TensorRT-LLM compiled ~30-50ms target、100ms hard ceiling)
- Fine-tune toolchain: HuggingFace + PEFT → NeMo framework + LoRA (NeMo SDK 経 fine-tune workflow)
- Deployment stack: HuggingFace transformers → TensorRT-LLM compiled engine + (optional) Triton Inference Server
- Tier-2 VL candidate: Qwen2.5-VL-7B-Instruct (production-mature) → NVIDIA NVLM (research-tier、Phase 2 で再検討、本 memo では explicit defer)
- Risk profile: NeMo / TensorRT-LLM Nemotron 統合 maturity を新 risk として §7 で明記

---

## §1 Architecture (Nemotron Mini 4B specs + classifier head)

### 1.1 Variant 比較 (Nemotron Mini 4B vs Qwen2.5-0.5B vs API fallback)

| Variant | Params / VRAM (INT4) / Latency | Source | THREAD fit |
|---------|-------------------------------|--------|-------------|
| **Nemotron Mini 4B Instruct** (TensorRT-LLM compiled INT4) | 4B / ~2 GB INT4 (estimated) / ~30-50 ms TensorRT compiled (estimated) | NVIDIA HuggingFace model card (verified): emb 3072, MLP 9216, GQA, RoPE, ctx 4096, base = Minitron-4B = pruned Nemotron-4 15B | **Tier-1 primary** (Rs γ disposition、§0 rationale 4 reasons) |
| Qwen2.5-0.5B (text-only fine-tuned) | 0.5B / ~0.5 GB INT4 / 22 ms native (NVIDIA Jetson 検証済) | Qwen2.5 model card (verified) + LL-WorldModel-Feasibility §7 | **Superseded** (Qwen design 経 historical baseline、本 memo では reference のみ) |
| Qwen2.5-VL-7B-Instruct INT4 | 7.6B / ~6 GB INT4 / ~150-200 ms (estimated) | Qwen2.5 model family card | Phase 2 vision proposer Tier-2 候補 (本 memo では deferred、§1.4 参照) |
| NVIDIA NVLM (vision Tier-2 候補) | ~70B / ~35 GB INT4 (estimated) / ~500-1000 ms (estimated) | NVIDIA research release (estimated, no direct source) | Phase 2 deferred、Qwen2.5-VL-7B より risk 高 (research-tier、production maturity 不足) |
| API fallback (Anthropic Claude / OpenAI GPT-4o-mini) | n/a | Network 依存 | Gate 2 batch eval 用途のみ、production loop 不可 |

**Verified facts (HuggingFace Nemotron-Mini-4B-Instruct model card)**:
- Architecture: Transformer Decoder, Grouped-Query Attention (GQA), Rotary Position Embeddings (RoPE)
- Embedding size: 3072, MLP intermediate: 9216, Attention heads: 32, Context length: 4096
- Base model lineage: Nemotron-4 15B → (pruned + distilled) → Minitron-4B-Base → (instruct fine-tune) → Nemotron-Mini-4B-Instruct
- Training period: 2024-02 to 2024-08
- License: NVIDIA Community Model License (Aug 2024)
- Recommended deployment: Transformers, NeMo, PyTorch (TensorRT-LLM not explicit in model card README、後述 §2 で TensorRT-LLM 経路は estimated)
- Intended use cases: Roleplay, RAG QA, function calling, on-device deployment

**Estimated facts (no direct source、本 env からは TensorRT-LLM / NeMo doc fetch blocked)**:
- TensorRT-LLM Nemotron Mini 4B INT4 VRAM ~2 GB (typical 4B INT4 ratio ~0.5 GB/B 経の linear extrapolation)
- TensorRT-LLM compiled latency 30-50 ms (HuggingFace native ~80-150ms × TensorRT-LLM 2-3x speedup の estimate)
- TensorRT-LLM `trtllm-build` compilation time 1-2 hours (4B model class typical)

### 1.2 推奨: Tier-1 Nemotron Mini 4B (proprio-only fault classifier、TensorRT-LLM compiled)

- **Phase 1 (本 memo scope)**: Tier-1 Nemotron Mini 4B INT4 + TensorRT-LLM compiled engine、proprio + log_per_world feature classification only
- **Phase 2 (本 memo deferred、CC#5 vision integration 後)**: Tier-2 vision-aware recovery proposer、Qwen2.5-VL-7B-Instruct (production-mature) を default 候補に維持、NVIDIA NVLM は research-tier risk noted で defer

Phase 2 deferred 理由:
- CC#5 MVP-2B (vision-policy fusion) 完成 dependency (LL-WorldModel-Feasibility Step 7 line 322-326 制約整合)
- NVLM はまだ research release、THREAD production loop に直接 deploy する maturity 評価不足
- Qwen2.5-VL-7B は既に Qwen design でも default、本 memo の Tier-1 model 切替と独立に Tier-2 候補は変わらず

### 1.3 GPU resource 計画 (CLAUDE.md GPU 規約遵守)

| GPU | Process | Nemotron Mini 4B allocation | Free margin |
|-----|---------|------------------------------|-------------|
| cuda:0 (RTX A6000 48GB) | Isaac Sim / Newton (12-15 GB) + (optional) Tier-2 VL (Phase 2、~6 GB INT4) | Nemotron INT4 ~2 GB を cuda:0 同居可能 | ~25-31 GB free (Tier-2 不在時)、~19-25 GB free (Phase 2 同居時) |
| **cuda:2 (RTX PRO 4000 Blackwell 24GB) [推奨]** | RL training (~12-18 GB) + **Nemotron Mini 4B INT4 (~2 GB)** | **Tier-1 classifier 同居 (~14-20 GB total、≥4 GB free)** | training peak 時 borderline、INT4 必須 (FP16 8GB は OOM risk) |

**推奨配置**: cuda:2 PRO 4000 Blackwell に Nemotron Mini 4B INT4 deploy (Qwen design §1.4 same allocation)。
- `CUDA_VISIBLE_DEVICES=2 python ...` で classifier 限定起動
- training process との VRAM 競合は INT4 quantization で mitigate (FP16 8GB は cuda:2 で training と共存不可)
- cuda:0 は Isaac Sim / Newton 占有 + Phase 2 で Tier-2 vision proposer 候補のため、Tier-1 classifier は cuda:2 に寄せる

**FP16 → INT4 quantization 必須化**: Qwen 0.5B は cuda:2 で FP16 1GB 余裕、Nemotron 4B FP16 8GB は cuda:2 PRO 4000 Blackwell の training peak (~18GB) との合計 ~26GB が VRAM 24GB 超過、INT4 ~2GB が production deployment の唯一 viable path。

### 1.4 Deployment options 比較

| Method | Pros | Cons | 推奨 |
|--------|------|------|------|
| **TensorRT-LLM compiled engine + Python API** | NVIDIA hardware native、INT4/INT8/FP8 quantization 標準、compiled latency 最速 (estimated 2-3x HuggingFace) | NeMo + TensorRT-LLM install heavy、`trtllm-build` 1-2h compilation overhead、API maturity 検証要 | **primary** (Rs γ disposition core motivation) |
| HuggingFace transformers (debug fallback) | Python integration 直接、compilation 不要、debug loop 短 | latency 80-150 ms estimated (compiled の 2-3x slow)、INT4 quantization は bitsandbytes 必要 | **secondary** (debug + A1 fine-tune validation phase) |
| Triton Inference Server (TensorRT-LLM backend) | 多 tenant 同時 serving、HTTP API standard、production-grade monitoring | HTTP roundtrip 1-3 ms NW overhead、orchestrator hook が in-process より複雑 | **optional** (multi-process deployment 必要時のみ、本 design では in-process TensorRT-LLM primary) |
| vLLM (third-party) | 高 throughput、Qwen design baseline | NVIDIA stack ecosystem 外、Nemotron 統合 maturity 不明 | **defer** (Rs γ NVIDIA native 方針と整合せず) |

**推奨**: TensorRT-LLM compiled engine in-process primary、HuggingFace transformers fallback (debug + fine-tune validation)、Triton は production multi-tenant 必要時のみ。

---

## §2 Inference stack (TensorRT-LLM specifics)

### 2.1 Compilation flow (HuggingFace ckpt → TensorRT-LLM engine)

```
Phase A1 fine-tune output: <ckpt-path>/<lora-or-merged>/
    ↓ (NeMo export、`nemo.export.tensorrt_llm`、estimated workflow)
NeMo intermediate format
    ↓ (`trtllm-build --checkpoint_dir <nemo-out> --output_dir <engine-dir> --gemm_plugin float16`)
TensorRT-LLM engine.plan + tokenizer + config.json
    ↓ (Phase A2 orchestrator hook で load)
RoutingOrchestrator.cascade_c LLMFaultClassifier
```

**Estimated steps (no direct source、TensorRT-LLM doc fetch blocked from this env)**:
- NeMo `nemo.export.tensorrt_llm.MegatronGPTExporter` で HuggingFace ckpt → NeMo → TRT-LLM engine 経路 (NeMo framework typical workflow)
- `trtllm-build` CLI args: `--gemm_plugin float16 --gpt_attention_plugin float16 --remove_input_padding enable --use_paged_kv_cache enable --quant_type W4A16` (INT4 weight + FP16 activation 推奨)
- Build artifact: `<engine-dir>/rank0.engine` + `config.json` + tokenizer (~2 GB INT4 + tokenizer ~1 MB)

### 2.2 Latency budget breakdown (target ≤ 100ms p95)

| Component | Estimated latency | Source |
|-----------|---------------------|--------|
| Compilation (one-time) | 1-2 hours `trtllm-build` | estimated, no direct source |
| TensorRT-LLM engine load (per-process startup) | 10-30 sec | estimated, no direct source |
| **Inference per prompt (compiled INT4)** | **30-50 ms** | estimated, no direct source (HuggingFace native ~80-150ms × 2-3x speedup expected) |
| JSON parse + dispatcher overhead | < 5 ms | Python dict ops typical |
| Total per-attempt budget | **35-55 ms target、100 ms hard ceiling** | Gate 2 PASS criterion (本 memo §6.1 verbatim) |

**Margin analysis**: 35-55 ms estimated × 2 (worst-case p99) = 70-110 ms、p95 100ms hard ceiling 内 borderline。Risk mitigation §7 R5 で扱う (alarm at 80ms threshold)。

### 2.3 Quantization 推奨

- **INT4 weight + FP16 activation (W4A16、AWQ または GPTQ)**: 推奨 default、~2 GB VRAM 達成、accuracy degradation < 1% (estimated, 4B class typical)
- **INT8 weight + FP16 activation (W8A16)**: fallback、~4 GB VRAM、accuracy degradation < 0.5%
- **FP16 baseline**: ~8 GB VRAM、cuda:2 training と共存不可、debug 用のみ

**INT4 vs INT8 選択基準**: A1 phase で synthetic bench (5 mode × 4 skill = 400 sample) で INT4 と INT8 の accuracy 差を ≤ 1% で確認、≤ 1% なら INT4 default、> 1% なら INT8 fallback。Gate 2 PASS condition (≥ 0.60 aggregated) は absolute 値、quantization degradation で boundary 割り込みが起きる場合 INT8 採用。

### 2.4 Python integration (擬似 code、impl は CC-T-WM-G2-A2 で本実装)

```python
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Cascade C LLM fault classifier (Nemotron Mini 4B + TensorRT-LLM compiled).

Pseudo-code (impl: CC-T-WM-G2-A2). Mirrors Qwen design vault entry §"接続箇所詳細"
adapted for TensorRT-LLM Python API.
"""

from pathlib import Path
import json

import torch
import tensorrt_llm  # estimated import path, no direct source verified from this env
from tensorrt_llm.runtime import GenerationSession, ModelRunner  # estimated API surface

from thread_isaac_lab.skills.result import SkillName, SkillResult


class LLMFaultClassifier:
    """Tier-1 Nemotron Mini 4B + TensorRT-LLM Cascade C classifier.

    Phase 1 (this design): Tier-1 only (proprio + log_per_world feature classifier).
    Phase 2 (deferred, CC#5 vision integration): Tier-2 VL proposer extension hook.
    """

    def __init__(
        self,
        engine_dir: Path,
        tokenizer_dir: Path,
        device: str = "cuda:2",
        max_new_tokens: int = 256,
    ):
        """Load TensorRT-LLM compiled engine.

        Args:
            engine_dir: Path to ``<engine-dir>`` containing ``rank0.engine`` + ``config.json``
                produced by ``trtllm-build`` (Phase A1 fine-tune + compile output).
            tokenizer_dir: Path to tokenizer directory (HuggingFace format).
            device: CUDA device ID (default ``cuda:2`` per CLAUDE.md GPU §3 allocation).
            max_new_tokens: Generation budget for JSON verdict (256 typical).
        """
        # Estimated API (no direct source verified from this env, see §7 R1)
        self.runner = ModelRunner.from_dir(
            engine_dir=str(engine_dir),
            tokenizer_dir=str(tokenizer_dir),
            rank=0,
        )
        self.device = device
        self.max_new_tokens = max_new_tokens

    def classify(self, obs: dict, log_per_world: dict) -> dict:
        """Return verdict JSON per Qwen design §3.1 (b) schema (inherited).

        Returns:
            verdict dict with keys: ``verdict`` (OK | PRE_FAIL_DETECTED | OOD_HIGH |
            RECOVERY_PROPOSE), ``confidence`` (0.0-1.0), ``failure_mode`` (F1-F7),
            ``recommended_action`` (skill_override / retry_seed_override /
            scripted_fallback / rollback_depth_hint), ``reasoning`` (debug log).
        """
        prompt = self._build_prompt(obs, log_per_world)
        # TensorRT-LLM generation (estimated API)
        outputs = self.runner.generate(
            batch_input_ids=[self._tokenize(prompt)],
            max_new_tokens=self.max_new_tokens,
            temperature=0.1,  # low for structured JSON output stability
        )
        raw = self._detokenize(outputs[0])
        try:
            verdict = json.loads(self._extract_json(raw))
        except json.JSONDecodeError:
            # fallback: reject malformed → no override (Cluster G default path)
            return {"verdict": "OK", "confidence": 0.0, "reasoning": "JSON parse fail"}
        return verdict

    def _build_prompt(self, obs: dict, log_per_world: dict) -> str:
        """Format obs + log_per_world into structured prompt (impl A1 fine-tune format)."""
        # impl: CC-T-WM-G2-A1 で fine-tune dataset format と整合
        ...

    def _tokenize(self, prompt: str) -> list[int]:
        ...

    def _detokenize(self, token_ids: list[int]) -> str:
        ...

    def _extract_json(self, raw: str) -> str:
        """Strip generation tail, isolate JSON block."""
        ...


def cascade_c_dispatch(
    verdict: dict,
    default_step_id: int,
) -> tuple[SkillName | None, int | None, bool]:
    """Map LLM JSON verdict to (skill_override, retry_seed, scripted_fallback).

    Inherited verbatim from Qwen design §3.1 (b) (model-independent).

    Returns:
        (skill_override: SkillName | None, retry_seed: int | None, scripted_fallback: bool)
    """
    if verdict.get("verdict") == "OK" or verdict.get("confidence", 0.0) < 0.85:
        return (None, None, False)  # Cluster G default path
    rec = verdict.get("recommended_action", {})
    skill_str = rec.get("skill_override")
    skill_override = SkillName[skill_str] if skill_str else None
    return (skill_override, rec.get("retry_seed_override"), rec.get("scripted_fallback", False))


# RoutingOrchestrator.execute_step modification (~30-50 LoC、L1050 attempt loop):
#   for attempt in range(self.MAX_RETRY + 1):
#       if attempt > 0 and self.cascade_c is not None:  # NEW
#           obs, _ = self.env.get_observations()
#           log_per_world = self._extract_log_per_world()
#           verdict = self.cascade_c.classify(obs, log_per_world)
#           skill_override, retry_seed_override, scripted_fb = cascade_c_dispatch(
#               verdict, step_id
#           )
#           if retry_seed_override is not None:
#               base_seed = retry_seed_override  # override C7 default
#       if attempt > 0:
#           torch.manual_seed(base_seed * 1000 + attempt)  # existing C7 seed perturbation
#       result = self.execute_skill(step_id, max_rl_steps=max_rl_steps)
#       ...  # existing Cluster G path
```

### 2.5 TensorRT-LLM version pin 推奨

- **推奨 pin**: TensorRT-LLM v0.13+ (estimated latest stable as of 2026-05、no direct source verified)、Nemotron model class support 含む安定 release を A1 phase で確認
- **CUDA / driver version**: CUDA 12.4+ + driver 550+ 推奨 (estimated、TensorRT-LLM 4B model class typical)
- **Python**: 3.10 / 3.11 (NeMo + TensorRT-LLM compatible)

A1 fine-tune phase 開始時に TensorRT-LLM release notes を再確認、Nemotron Mini 4B explicit support 有無を verify (現状は estimated)。

---

## §3 Dataset design (inherit from Qwen)

Dataset design は **model-agnostic**、Qwen design §4.2 Track 1/Track 2 を本 memo では full inherit。本 §3 は brief reference のみ、duplicate せず。

- **Track 1 synthetic failure injection**: 5 failure mode × 4 skill = 20 buckets × ~80 sample = ~400 sample (test fixture 経 controlled inject、env step 不要、wall ~5-10 min)
  - 詳細: Qwen design memo §4.2 Track 1 (`project_l1e_cascade_c_qwen_design_complete_2026-04-27.md` line 308-322)
- **Track 2 real failure detection**: Phase 5-2 G5 wet-run logs (~100 episode、~50 failure event 見込) + Phase 5-3 短期 milestone 経験 logs、manual annotation (CC + Rs combined verify)
  - 詳細: Qwen design memo §4.2 Track 2 (line 324-332)
- **Aggregation**: 0.7 × synthetic + 0.3 × real for Gate 2 evaluation (Qwen design §4.3 verbatim)

**Nemotron 切替で dataset 影響なし**: dataset format は Nemotron Mini 4B context 4096 token に収まる構造 (Qwen2.5-0.5B context 32768 と互換、prompt 短縮不要)、proprio + log_per_world feature → 7-class label (OK + F1-F7) は model-independent。

**Inheritance scope (Qwen design §4.2 ほぼ全 reuse)**: 5 failure mode definition + injection method + sample 数 + accuracy formula + 7-class output schema。Nemotron 用に変更する点は **prompt format のみ** (Nemotron tokenizer 経の chat template、HuggingFace `apply_chat_template` 経で format)、A1 phase で format adapter ~20 LoC 追加。

---

## §4 Fine-tune procedure (NeMo framework)

### 4.1 NeMo framework workflow

```
Phase A1 入力: HuggingFace ckpt nvidia/Nemotron-Mini-4B-Instruct + dataset (A0 output)
    ↓ (NeMo HuggingFace import、`nemo.collections.llm.import_ckpt`)
NeMo native ckpt
    ↓ (NeMo PEFT LoRA fine-tune、`nemo.collections.llm.gpt.peft.lora`)
LoRA-tuned ckpt (delta weight only)
    ↓ (merge or export-as-LoRA、impl 選択)
HuggingFace-compatible ckpt または LoRA adapter
    ↓ (§2.1 NeMo → TensorRT-LLM export)
TensorRT-LLM engine (Phase A2 入力)
```

**Estimated workflow (no direct source、NeMo framework doc fetch blocked from this env)**:
- NeMo PEFT LoRA module は `nemo.collections.llm.gpt.peft` 配下 (NeMo framework standard pattern)
- HuggingFace ckpt import は `nemo.collections.llm.import_ckpt(ckpt="nvidia/Nemotron-Mini-4B-Instruct")` 経 (estimated API、NeMo public docs 経で要確認)
- LoRA export: NeMo native format → HuggingFace PEFT-compatible format converter、impl phase で具体 API 確定

### 4.2 Hyperparameter precedent (estimated baseline、A1 phase で empirical 確定)

| Hyperparameter | 推奨初期値 | Source (estimated unless cited) |
|----------------|------------|----------------------------------|
| Batch size | 8-16 | estimated, no direct source (4B model on PRO 4000 Blackwell 24GB tier typical) |
| Learning rate | 1e-4 to 5e-5 | estimated, no direct source (LoRA 4B class typical) |
| Epochs | 3-5 | estimated, no direct source |
| LoRA rank (r) | 16-32 | estimated, no direct source (instruct fine-tune typical) |
| LoRA alpha | 32-64 (rank × 2) | estimated, no direct source |
| LoRA target modules | q_proj, k_proj, v_proj, o_proj (attention only initial) | estimated, no direct source (Nemotron-4 GQA arch typical) |
| Sequence length | 1024-2048 (Nemotron ctx 4096 を上限としない) | verified Nemotron ctx limit 4096 (HuggingFace model card) |
| Gradient accumulation | 2-4 | estimated (4B class memory peak mitigation) |
| Mixed precision | bf16 | estimated (PRO 4000 Blackwell native bf16 support) |
| Gradient checkpointing | enable | estimated (4B fine-tune VRAM peak mitigation必須 on 24GB) |

**A1 phase での empirical confirmation 必須**: 上記 8 hyperparameter は published 4B model fine-tune precedent からの extrapolation、THREAD dataset (~400 sample) 規模での optimal 値は未検証。A1 phase 初期で 2-3 trial 実施、validation accuracy が ≥ 0.50 (Gate 2 0.60 の中間 milestone) に達するまで sweep。

### 4.3 Training cost re-estimate vs Qwen 0.5B

| Item | Qwen 0.5B baseline (Qwen design §5.1) | Nemotron 4B estimate (本 memo) | Scaling ratio |
|------|----------------------------------------|--------------------------------|---------------|
| CC time (script + dataset adapt + train + eval) | ~10h | ~10-15h (dataset Qwen 流用 + Nemotron prompt adapter ~20 LoC + NeMo workflow setup +5h) | +0-50% |
| GPU time (fine-tune + checkpoint save) | ~5h | ~10-15h | +100-200% |
| Total wall (CC + GPU sequential) | ~15h | ~20-30h | +33-100% |

**Scaling rationale (linear+ assumption)**:
- Model size 8x (0.5B → 4B、param count ratio)
- LoRA fine-tune は full SFT より cheaper、fine-tune cost は param count に対し sub-linear (LoRA は trainable param が rank × hidden size のみ、~1-3% of model)
- Dataset size 一定 (Qwen 流用、~400 sample × Track 2)、step 数 ~ epoch × dataset / batch ~constant
- 結果: GPU time scaling は ~2-3x (model fwd/bwd cost が 8x だが LoRA + bf16 + grad checkpointing で実測 2-3x が典型)

**Risk**: NeMo framework 経 fine-tune は HuggingFace + PEFT 経より setup overhead が大、A1 phase wall 上振れ +50% が realistic upper bound。`feedback_long_task_progress_observability` 適用 (unbuffered log + monitor + 早期 abort 基準必須)。

### 4.4 Evaluation during fine-tune

- **Held-out validation accuracy**: training dataset を 80/20 split、20% を validation set として each epoch end で 7-class accuracy measure
- **Early stopping**: validation accuracy が 3 epoch 連続で ≥ 0.5% delta なし → fine-tune 終了
- **BiCICLe Straighten Rope 34.3% low bar**: validation accuracy が ≥ 0.40 を 第 1 milestone (低 bar、deformable cable LLM precedent threshold)、≥ 0.60 を Gate 2 candidate ckpt
- **TensorRT-LLM 経 quantization degradation check**: fine-tune 完了後、HuggingFace baseline (FP16) vs TensorRT-LLM compiled INT4 で synthetic bench (400 sample) accuracy 差 ≤ 1% 確認、超過時 INT8 fallback

---

## §5 Integration plan (orchestrator hook, API surface)

### 5.1 Cluster G floor unchanged 確認

env / scripted_skills / step_table / SkillResult enum / Snapshot cascade は **不変**、orchestrator side のみ `execute_step` pre-attempt hook + `_rollback` の bc_p0_region_check 拡張で injection。Qwen design §5.3 と完全同一、Nemotron 切替で影響なし。

| Cluster G component | File / line | 変更 / 不変 |
|---------------------|-------------|--------------|
| `RoutingOrchestrator.execute_skill` | `orchestrator/routing_orchestrator.py` L862-899 | **不変** |
| `RoutingOrchestrator._run_rl_episode` | L901-943 | per-step polling hook injection 候補 (Phase 2 optional、~20 LoC) |
| **`RoutingOrchestrator.execute_step`** | L1002-1075 | **pre-attempt hook 追加のみ** (~30-50 LoC、§5.2 詳細) |
| `RoutingOrchestrator._rollback` | L1103-1153 | bc_p0_region_check 拡張 (~10 LoC、Tier-1 OOD high probability 検出時 False return) |
| `_PerArmClampTracker` (Phase C4 B5) | L453-534 | **不変** |
| `derive_clamp_r_skill_result` | L536-635 | **不変** |
| `derive_skill_result` | L372-422 | **不変** |
| `Snapshot cascade` (capture / restore) | L1184-1271 + `skills/snapshot.py` | **不変** |
| `SkillResult` enum (5 outcomes) | `skills/result.py` (25 LoC) | **不変** (Cascade C は SkillResult 上に layer) |
| `step_table.py` | `skills/step_table.py` | **不変** (env / scripted UNCHANGED 制約) |
| `scripted_skills.py` | `skills/scripted_skills.py` | **不変** |

### 5.2 Hook location pseudo-code (`execute_step` L1050 pre-attempt hook)

§2.4 で完全 pseudo-code 提示済、本 §5.2 では integration point + LoC budget のみ summary:

| Item | Detail |
|------|--------|
| Hook location | `RoutingOrchestrator.execute_step` L1050 `for attempt in range(self.MAX_RETRY + 1):` loop top |
| Existing code (不変) | C7 seed perturbation L1052 `torch.manual_seed(base_seed * 1000 + attempt)` |
| New code (pre-attempt) | `LLMFaultClassifier.classify(obs, log_per_world)` → `cascade_c_dispatch(verdict)` → `(skill_override, retry_seed_override, scripted_fallback)` |
| Override path | `retry_seed_override` 非 None 時 `base_seed = retry_seed_override`、その後 existing C7 が seed apply |
| Fallback path | verdict.confidence < 0.85 or verdict == "OK" で existing Cluster G path 完全 fallthrough (override なし) |
| LoC budget | hook 30-50 LoC + LLMFaultClassifier class 80-120 LoC (§2.4 pseudo-code) + dispatcher 20-30 LoC + test 50-80 LoC = **~180-280 LoC total** |

### 5.3 Verdict JSON schema (REUSE from Qwen design)

完全 inherit、Qwen design §3.1 (b) を本 memo §3 で reference。schema field 一覧:
- `verdict`: "OK" | "PRE_FAIL_DETECTED" | "OOD_HIGH" | "RECOVERY_PROPOSE"
- `confidence`: 0.0-1.0
- `failure_mode`: F1-F7 enum (Qwen design §2.1)
- `recommended_action`: { `skill_override`, `retry_seed_override`, `scripted_fallback`, `rollback_depth_hint` }
- `reasoning`: human-readable string (debug log only、orchestrator は使わない)

### 5.4 Failure mode coverage (REUSE from Qwen design §2.1)

F1-F7 全 7 failure mode は model-agnostic、Qwen design §2.1 verbatim 継承。Nemotron Mini 4B の 4B parameter 容量で Qwen 0.5B より理論的 capacity 上限が高く、F1-F7 distinction の learnability は **Nemotron 優位** が期待 (estimated, no direct source、Gate 2 bench 経の empirical 確認必要)。

| Failure mode | Cluster G coverage | Cascade C 補強 priority (Qwen design §2.1 整合) |
|--------------|---------------------|-------------------------------------------------|
| F1 explosion | EXPLOSION → abort | HIGH |
| F2 cable drop | CABLE_DROP → rollback (env extras key 未実装、現状 FAIL に subsume) | HIGH |
| F3 timeout | TIMEOUT → retry (MAX_RETRY=3、C7 seed perturbation) | MEDIUM |
| F4 partial success | FAIL → retry/rollback | HIGH |
| F5 reward hacking / OOD | bc_p0_region_check hook | MEDIUM |
| F6 cable slack / hook misalignment | 無し (proprio で観測不能) | LOW (Tier-2 vision、Phase 2 deferred) |
| F7 finger close fail | FAIL に subsume | MEDIUM |

---

## §6 Benchmark methodology (Gate 2 measurement)

### 6.1 Gate 2 official 定義

```
Gate 2 PASS = (classifier accuracy ≥ 0.60 aggregated)
              AND (TensorRT-LLM compiled latency ≤ 100ms p95)

where:
  accuracy aggregated = 0.7 × synthetic + 0.3 × real
  synthetic accuracy  = TP / (TP + FN) on 5 mode × 4 skill × 80 sample = 400 fixture
  real accuracy       = TP / (TP + FN) on G5 wet-run + Phase 5-3 manual annotation logs
  latency p95         = 95th percentile over 1000 inference cycle on representative
                        obs payload (RTX A6000 cuda:0 OR RTX PRO 4000 cuda:2)
```

- Accuracy formula: Qwen design §4.3 verbatim (model-independent)
- Latency criterion: **NEW addition** (Qwen design では 22 ms native で latency budget 言及のみ、Nemotron は compiled latency が runtime budget の load-bearing factor のため明示 hard ceiling 化)
- Reject case (Qwen design §4.3 verbatim):
  - synthetic > 0.60 but real < 0.40 → Gate 2 PARTIAL (Tier-2 vision proposer Phase 2 必要)
  - synthetic > 0.60 AND real > 0.60 → Gate 2 PASS (Cascade C 本番化、Phase 5-2+)
  - 両 < 0.60 → Gate 2 FAIL (Option D freeze、Phase 5-3 集中)
- Reject case (latency、本 memo NEW):
  - latency p95 ≤ 100ms → PASS
  - 100ms < latency p95 ≤ 150ms → PARTIAL (async polling alternative + budget alarm at 80ms 検討)
  - latency p95 > 150ms → FAIL (TensorRT-LLM quantization 強化 INT8→INT4 mandatory、または Qwen0.5B fallback 検討)

### 6.2 Accuracy measurement (REFERENCE Qwen §4.2)

完全 inherit、本 memo では duplicate せず。詳細は `project_l1e_cascade_c_qwen_design_complete_2026-04-27.md` §4.2 (Track 1 / Track 2) 参照。

Bench script: `eval_cascade_c_classifier.py` (A3 phase、~150-200 LoC、本 memo §6.4 で詳細)

### 6.3 Latency measurement protocol (NEW、本 memo Nemotron-specific)

| Item | Detail |
|------|--------|
| Bench script | `eval_cascade_c_classifier.py --measure-latency` (A3 phase で existing Qwen design A3 ~150-200 LoC に ~20 LoC 追加) |
| Sample size | 1000 inference cycle on representative obs payload (synthetic Track 1 から 1 sample 抽選、固定 prompt) |
| Metrics | p50, p95, p99, max, mean、std |
| Hardware | RTX A6000 cuda:0 (Isaac Sim 同居なし) + RTX PRO 4000 Blackwell cuda:2 (training 同居なし) の 2 baseline measure |
| Compilation time | 別途 measure (1000 inference cycle と分離、one-time cost、100ms budget には含めない) |
| Output | `cascade_c_eval_<run_id>/latency_report.json`: { p50, p95, p99, max, mean, std, hardware, sample_size, compilation_time } |
| Pass criterion | p95 ≤ 100ms hard ceiling、80ms warning threshold (alarm at runtime per §7 R5) |

### 6.4 Bench harness

```
thread_isaac_lab/scripts/eval_cascade_c_classifier.py  # 新規 (~170-220 LoC、Qwen A3 ~150-200 + Nemotron latency ~20)
  --classifier-engine <engine-dir>          # TensorRT-LLM engine path
  --classifier-tokenizer <tokenizer-dir>
  --track synthetic | real | both
  --skill AC | IC | AR | Grip | all
  --measure-latency                         # NEW、§6.3 protocol
  --output cascade_c_eval_<run_id>/
    metrics.json (accuracy / precision / recall per F1-F7 × per skill)
    confusion_matrix.png
    failure_log.jsonl (annotated TP/FP/FN/TN per sample)
    latency_report.json (NEW、§6.3 metrics)
```

Existing `eval_skill.py` (667 LoC、multi-skill unified) と integration 検討、ただし classifier eval は env step 不要 (synthetic) で別 entry 推奨 (Qwen design §4.4 整合、本 memo § で latency 軸追加)。

---

## §7 Risk analysis (Nemotron-specific)

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| R1 | TensorRT-LLM Nemotron Mini 4B support maturity 不明 (NVIDIA HuggingFace model card で TensorRT-LLM 明示なし、recent integration の可能性) | MEDIUM | HIGH (Phase A1 BLOCKED if TRT-LLM Nemotron build fails) | TensorRT-LLM version pin、HuggingFace transformers fallback path A2 で並行確保、Phase A1 開始時 release notes 再確認 (`feedback_check_existing_eval_grep` 経 KA0 拡張) |
| R2 | INT4 quantization accuracy degradation (Gate 2 boundary 割り込み risk) | MEDIUM | HIGH (≥ 0.60 aggregated boundary 失敗で Gate 2 FAIL) | A1 phase で synthetic bench (400 sample) 経 INT4 vs INT8 vs FP16 accuracy 差 ≤ 1% 確認、超過時 INT8 fallback。FP16 fallback は VRAM 制約で cuda:0 専用 |
| R3 | NeMo framework GPU memory peaks during fine-tune | HIGH | MEDIUM | LoRA only (full SFT 禁止)、gradient checkpointing enable、mixed precision bf16、batch size 8-16 上限、必要時 grad accumulation 4-8 |
| R4 | Triton Inference Server HTTP roundtrip overhead (1-3ms NW) | LOW (Triton optional) | LOW | in-process TensorRT-LLM primary、Triton は production multi-tenant 必要時のみ activate |
| R5 | Latency budget overrun at p95/p99 (compiled でも tail latency 不安定 risk) | MEDIUM | HIGH (Gate 2 latency criterion FAIL) | Budget alarm at 80ms threshold (orchestrator hook で latency monitor + warning log)、p99 110ms 超で async classifier polling alternative 検討、最後の手段 Qwen0.5B fallback |
| R6 | **Decommissioned Nemotron 30B-A3B AWQ (2026-04-10) との混同 risk** | LOW (本 memo で明示) | MEDIUM (誤 model 採用で Phase A0/A1 やり直し) | 本 memo §0 で明示 distinguish、Nemotron Mini 4B (本 memo) ≠ Nemotron 30B-A3B (`thread-vault/06-Knowledge/LL-NemotronVerifier.md` + `Nemotron-Nano-AWQ-vLLM.md` historical reference)。Phase A0 dataset prep 開始時に CC 自己 verify、`huggingface.co/nvidia/Nemotron-Mini-4B-Instruct` 直接 cite |
| R7 | NeMo framework install heavy (5-8h overhead) | HIGH | LOW | Phase A1 着手前に separate sub-task で NeMo container deploy、env_isaaclab6 venv との conflict 事前確認 |
| R8 | TensorRT-LLM compilation 1-2h cost が dev cycle を slow down | MEDIUM | LOW | A1 phase で fine-tune ckpt 1 個 produced after 全 hyperparameter sweep (sweep 中は HuggingFace native debug)、final ckpt のみ compile |

**P0 risk summary**:
- R1 (TensorRT-LLM Nemotron support maturity) と R5 (latency budget overrun) が Gate 2 FAIL 直結 risk、A1 phase 初期で必ず empirical confirm
- R2 (INT4 accuracy degradation) は accuracy boundary risk、A1 phase で multi-quantization sweep が必須
- R6 (decommissioned 30B との混同) は本 memo + state.md frontmatter の明示で mitigation 完了、A0 phase で再 verify

---

## §8 Cross-references

### 8.1 関連 file references (絶対 path)

| File | 用途 |
|------|------|
| `/home/rlrk/IsaacLab/thread_isaac_lab/orchestrator/routing_orchestrator.py` (1271 LoC、verified 2026-05-03) | Cluster G floor、Cascade C upstream extension target |
| `/home/rlrk/IsaacLab/thread_isaac_lab/skills/result.py` (25 LoC、verified 2026-05-03) | SkillResult enum (不変) |
| `/home/rlrk/IsaacLab/thread_isaac_lab/skills/snapshot.py` | Snapshot cascade (不変) |
| `/home/rlrk/IsaacLab/thread_isaac_lab/skills/scripted_skills.py` | scripted skill (不変) |
| `/home/rlrk/IsaacLab/thread_isaac_lab/skills/step_table.py` | STEP table (不変) |
| `/home/rlrk/IsaacLab/thread_isaac_lab/scripts/eval_skill.py` (667 LoC) | existing multi-skill eval、Cascade C bench は別 entry |
| `/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault/06-Knowledge/LL-WorldModel-Feasibility.md` (502 lines) | WM feasibility、§7-8 Cascade plan + Gate 1-4 |
| `/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault/06-Knowledge/LL-Cascade-C-Qwen-Design.md` (159 lines、SUPERSEDED) | Qwen design predecessor、historical reference |
| `/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault/06-Knowledge/LL-Orchestration-Design.md` | existing orchestrator architecture |
| `/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault/06-Knowledge/LL-Cosmos.md` | Cascade B 候補 (本 memo scope 外) |
| `/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault/06-Knowledge/FSM-LLM-Recovery.md` (24 lines) | historical context、FSM + LLM recovery layer initial concept |
| `/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault/06-Knowledge/LL-NemotronVerifier.md` | **decommissioned** 30B verifier (2026-04-10)、Nemotron Mini 4B とは別 model、§7 R6 distinguish reference |
| `/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault/06-Knowledge/Nemotron-Nano-AWQ-vLLM.md` | **decommissioned** Nano variant、§7 R6 distinguish reference |
| `/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault/T-WM-G2/state.md` | Gate 2 NEST node (本 memo の主 target)、§0 model choice + §1 Means table |
| `/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault/T-WM/state.md` | Umbrella node (capability axis、L1.E)、children = [T-WM-G1, T-WM-G2] |

### 8.2 Web research source URLs (verified)

| URL | Summary |
|-----|---------|
| https://huggingface.co/nvidia/Nemotron-Mini-4B-Instruct | NVIDIA official Nemotron Mini 4B Instruct model card: 4B params, GQA + RoPE, ctx 4096, base = Minitron-4B (pruned/distilled from Nemotron-4 15B), trained 2024-02 to 2024-08, NVIDIA Community Model License, recommended deployment = Transformers + NeMo + PyTorch (TensorRT-LLM not explicit). 本 memo §1.1 verified facts source |
| https://huggingface.co/Qwen/Qwen2.5-0.5B | Qwen2.5-0.5B base model card: 0.49B total / 0.36B non-embedding, 24 layers, GQA (14 query / 2 KV heads), context 32768, BF16, 29+ languages. 本 memo §1.1 superseded baseline reference |

### 8.3 Web research source URLs (blocked from this env、cite for future verification)

| URL | Reason / Status | Notes |
|-----|-----------------|-------|
| https://github.com/NVIDIA/TensorRT-LLM | WebFetch denied | TensorRT-LLM official repo、Phase A1 開始時 CC が再 verify (Nemotron explicit support、`trtllm-build` flags、Python API stability) |
| https://nvidia.github.io/TensorRT-LLM/ | WebFetch denied | TensorRT-LLM official docs、同上 |
| https://github.com/NVIDIA/NeMo | WebFetch denied | NeMo framework official repo、Phase A1 で fine-tune workflow + Nemotron import pattern verify |
| https://docs.nvidia.com/nemo-framework/user-guide/latest/ | WebFetch denied | NeMo framework user guide、同上 |
| https://developer.nvidia.com/blog/nvidia-nemotron-mini-4b-instruct-now-available-for-on-device-inference/ | WebFetch denied | NVIDIA developer blog、deployment recommendations + latency benchmarks の primary source 候補 |
| https://build.nvidia.com/nvidia/nemotron-mini-4b-instruct | WebFetch denied | NVIDIA NIM endpoint、official deployment latency reference |
| https://arxiv.org/abs/2407.14679 | WebFetch denied | Minitron pruning + distillation paper (Nemotron Mini 4B 親論文)、academic reference |
| https://arxiv.org/abs/2402.16819 | not attempted | Nemotron-4 15B (Nemotron Mini 4B 祖父 model) 論文 |

**Web research note**: 本 memo は HuggingFace model card 2 件 (Nemotron Mini 4B + Qwen2.5-0.5B) のみ verified、TensorRT-LLM / NeMo / NVIDIA developer blog は本 env から fetch denied。estimated facts は §1-§4 内で `(estimated, no direct source)` 明示、A1 phase 開始時 CC が release notes + GitHub repo (Bash `gh` または manual) で再 verify を必須化。

### 8.4 Authority + decision provenance

- **Rs γ disposition source (2026-04-29)**: L0-Coordinator#s4 chat、`~/.claude/projects/-home-rlrk-IsaacLab/memory/handoff_cc_l1e_node_creation_predispatch_2026-04-29.md` (predispatch handoff) + 本 memory index (project_nest_architecture.md、T-WM 起票 entry)
- **L1.E predispatch 7-CC Pre-Debate Option β verdict**: `~/.claude/projects/-home-rlrk-IsaacLab/memory/handoff_cc_l1e_node_creation_predispatch_2026-04-29.md` (39 challenges、3 multi-CC consensus issues 修正済 Revised PROPOSE)
- **Qwen design canonical memo (predecessor)**: `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_l1e_cascade_c_qwen_design_complete_2026-04-27.md` (32KB、465 lines)、本 memo の structural template
- **WM feasibility canonical**: `thread-vault/06-Knowledge/LL-WorldModel-Feasibility.md` §7 (LLM-Orchestrator impl spec) + §8 (Cascade plan + Gates 1-4、machine-decidable criteria)
- **G1 cross-skill 86% gap analysis (criticality elevation)**: `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_cross_skill_86pct_gap_analysis_2026-04-27.md`
- **L0-Coordinator role boundary (γ-1 minimal update path source)**: `~/.claude/projects/-home-rlrk-IsaacLab/memory/feedback_l0_coordinator_option_routing.md`

### 8.5 Future work pointers (impl spawn 時起票)

- **CC-T-WM-G2-A0** (Dataset prep) — 本 memo §3 + Qwen design §4.2 流用、~10-15h CC、~150 LoC
- **CC-T-WM-G2-A1** (Nemotron NeMo fine-tune + TensorRT-LLM build) — 本 memo §4 + §2.1、~10-15h CC + 10-15h GPU、~250 LoC
- **CC-T-WM-G2-A2** (Orchestrator hook、TensorRT-LLM Python API) — 本 memo §5 + §2.4、~8-12h CC、~100-150 LoC
- **CC-T-WM-G2-A3** (Gate 2 bench、accuracy + latency dual-metric) — 本 memo §6、~5-7h CC + ~3h GPU、~170-220 LoC
- **L1.E.2-Tier-2-VL-Spike** (Phase 2 deferred、CC#5 vision integration 後) — Qwen2.5-VL-7B-Instruct primary、NVLM defer。本 memo scope 外

---

## §9 別 task 起票候補 (CC dispatch、Nemotron 版)

Qwen design §5.2 を Nemotron 用に adapt。各 task は launch instruction template (Qwen design §"CC dispatch 用 Goal / Purpose / Role template" 経) で起票。

| Task ID | Phase | LoC est | Wall (CC + GPU) | Trigger / Dependency |
|---------|-------|---------|-----------------|------------------------|
| **CC-T-WM-G2-A0** | A0 dataset prep | ~150 LoC (test fixture + harvest script) | ~10-15h CC | 本 memo merge 後、Phase 5-2 G5 wet-run COMPLETE 待ち (Track 2 real failure logs)、Track 1 synthetic は先行可能 |
| **CC-T-WM-G2-A1** | A1 Nemotron fine-tune (NeMo + LoRA + TensorRT-LLM build) | ~250 LoC (train script + NeMo import + trtllm-build wrapper) | ~10-15h CC + ~10-15h GPU | A0 完了 + GPU resource (cuda:2 PRO 4000 24GB INT4 fit、cuda:0 余力) + NeMo install (~5-8h overhead) |
| **CC-T-WM-G2-A2** | A2 orchestrator hook (TensorRT-LLM Python API integration) | ~100-150 LoC (LLMFaultClassifier + cascade_c_dispatch + execute_step pre-attempt hook + test) | ~8-12h CC | A1 完了 (engine.plan + tokenizer 必要)、env / scripted_skills file UNCHANGED 制約遵守 (本 memo §5.1) |
| **CC-T-WM-G2-A3** | A3 Gate 2 bench (accuracy + latency dual-metric) | ~170-220 LoC (eval_cascade_c_classifier.py + latency measurement) | ~5-7h CC + ~3h GPU | A1 + A2 完了、Track 1 synthetic accuracy + Track 2 real (G5 wet-run logs) + latency p95 measure |

**Recommended 起票順序** (Qwen design §5.2 整合、Nemotron 切替で順序不変):
1. **CC-T-WM-G2-A0** (dataset prep、A1 必須前提)
2. **CC-T-WM-G2-A1** (Nemotron fine-tune + TensorRT-LLM build、core deliverable)
3. **CC-T-WM-G2-A3** (Gate 2 bench、accuracy + latency PASS/FAIL 判定 unlock)
4. **CC-T-WM-G2-A2** (orchestrator hook、A1 + A3 baseline 確立後 production integration)

(Phase 2 Tier-2 VL spike は CC#5 vision integration + Gate 2 PARTIAL/PASS で起票判断、本 memo defer)

**Total impl est (A0-A3)**: ~33-49h CC + ~13-18h GPU = **~46-67h wall** (Qwen baseline ~33-43h CC + ~13-23h GPU の +15-30%、§4.3 scaling 整合)

---

## §10 状態 update record + Caveats

### 10.1 状態 update record

- **2026-05-03 ~12:13 JST (起票)**: 本 design memo 起票 (640 lines、Rs γ disposition 経 2026-04-29 supersedes Qwen design)、L1.E.2 Cascade C active design canonical 化、A0-A3 別 task 起票候補 4 件提示
- **2026-05-03 ~12:13 JST (finalize)**: Rs delegation 経 disposition 4 Q (task spawn 順序 / latency PARTIAL fallback / NeMo install isolation / Tier-2 VL re-eval) を全件 impl spawn 各 task 内 再評価で defer 確定、Layer 2 post-Debate も Rs override 継続で skip (Day 1-5 precedent 準拠)、NEST cascade 追補は manifest COORD pane 既反映で不要、本 memo を `status: ready_for_impl_spawn` で finalize. Phase 2 impl spawn 待機 standby に移行 (CC-T-WM-G2-A0/A1/A2/A3 起票 trigger 待ち)

### 10.2 Caveats

- **TensorRT-LLM compilation overhead**: 1-2 hours one-time `trtllm-build` cost (estimated)、A1 phase fine-tune wall に含めない (separate from runtime budget per §6.1 latency criterion)
- **NeMo framework install overhead**: 5-8 hours (estimated)、Phase A1 着手前に separate sub-task で env_isaaclab6 venv との conflict 事前確認推奨 (§7 R7)
- **Decommissioned Nemotron 30B-A3B AWQ (2026-04-10) は別 model**: Nemotron Mini 4B (本 memo) ≠ Nemotron-30B-A3B (`LL-NemotronVerifier.md` + `Nemotron-Nano-AWQ-vLLM.md` historical)、§7 R6 で distinguish 明示済
- **Rs γ disposition trade-off accepted**: latency overhead (Qwen 22ms native → Nemotron ~30-50ms TensorRT compiled estimated)、ecosystem benefits (NVIDIA stack native + Triton 統合 + reward model 将来 reuse) と引き換え
- **Tier-2 VL deferred**: NVIDIA NVLM (research-tier) は Qwen2.5-VL-7B-Instruct (production-mature) より risk 高、Phase 2 で再検討 (本 memo scope 外)
- **Web research limitation**: TensorRT-LLM / NeMo / NVIDIA developer blog の primary source は本 env から fetch denied、§1-§4 estimated facts は A1 phase 開始時 CC が再 verify (release notes + GitHub repo manual cite) 必須
- **Empirical validation pending**: Phase A1 fine-tune 完了 + A3 Gate 2 bench で initial accuracy + latency baseline 確立まで、本 memo は design intent + impl roadmap、empirical numbers は est のみ
- **Cluster G LoC 1271 confirmed at 2026-05-03** (re-verify post-Qwen design 2026-04-27 snapshot で同値)、env / scripted_skills / step_table file UNCHANGED 制約遵守継続
- **Qwen design memo 不変保持**: 2026-04-29 supersedence note 追加済 (in-place、archive せず)、historical reference + impl roadmap 比較 baseline として継続参照可能
- **本 memo の更新権限**: model-independent components (dataset / JSON schema / Gate 2 PASS formula / hook injection point) は将来 model 切替 (Phase 2 NVLM 採用等) でも reuse、本 memo §0 inheritance map で明示済

