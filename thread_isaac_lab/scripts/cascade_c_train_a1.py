#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Cascade C A1 NeMo / HF LoRA fine-tune for Nemotron Mini 4B fault classifier.

Reads ``data/cascade_c_dataset_v0/dataset.jsonl`` (400 samples, SHA pinned in
manifest.json) and produces a LoRA adapter + ``val_metric.json`` under
``data/cascade_c_train_a1_run/``.

Architecture: HuggingFace ``transformers`` + ``peft`` LoRA (rank 16, alpha 32,
dropout 0.05, target all linear) on bf16, gradient checkpointing enabled, on
``nvidia/Nemotron-Mini-4B-Instruct``. ``Trainer`` from ``transformers``
manages the loop. The prompt-format adapter
(``cascade_c_prompt_adapter.to_training_pair``) is the only project-side
prompt-format dependency — both train and eval go through it for parity.

Hyperparams follow T-WM-G2-A1-Setup §2.2 / state.md §1 step 6: rank 16,
alpha 32, dropout 0.05, batch 8, grad accum 2, LR 3e-4, epochs 3,
max_seq_len 1024, bf16, grad checkpointing, AdamW, cosine warmup.
``--seed`` pins the 80/20 train/val split and torch RNG.

val_metric.json: aggregate accuracy (strict verdict+failure_mode match) +
loss curve summary + per-skill SR breakdown. Phase 1 P1 grant trigger is
``val_metric.json::accuracy >= 0.40``. <0.40 → Q6 ABORT chain.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

THREAD_ROOT = Path(__file__).resolve().parents[1]
if str(THREAD_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(THREAD_ROOT / "scripts"))

from cascade_c_prompt_adapter import (  # noqa: E402
    NEMOTRON_MINI_4B,
    format_completion,
    parse_completion,
    to_messages,
    to_training_pair,
)


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    import numpy as np

    np.random.seed(seed)
    import torch

    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def _load_jsonl(path: Path) -> list[dict]:
    samples: list[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples


def _stratified_split(
    samples: list[dict], val_frac: float, seed: int
) -> tuple[list[dict], list[dict]]:
    """Per-(skill,failure_mode) stratified split for stable val coverage."""
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for s in samples:
        buckets[(s["skill"], s["failure_mode_gt"])].append(s)
    rng = random.Random(seed)
    train: list[dict] = []
    val: list[dict] = []
    for key in sorted(buckets):
        items = buckets[key][:]
        rng.shuffle(items)
        n_val = max(1, int(round(len(items) * val_frac)))
        val.extend(items[:n_val])
        train.extend(items[n_val:])
    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


def _build_text_pair(sample: dict, tokenizer: Any) -> tuple[str, str]:
    """Return (prompt, completion) with model-specific chat-template applied.

    ``apply_chat_template`` with ``add_generation_prompt=True`` produces the
    full prompt that ends at the assistant's turn boundary; the completion is
    the bare JSON string. Loss is masked over the prompt at tokenization.
    """
    messages = to_messages(sample, format_name=NEMOTRON_MINI_4B)
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    completion = format_completion(sample, format_name=NEMOTRON_MINI_4B)
    return prompt, completion


def _tokenize_with_completion_mask(
    prompt: str,
    completion: str,
    tokenizer: Any,
    max_seq_len: int,
) -> dict[str, list[int]]:
    """Tokenize prompt+completion; mask prompt tokens in labels (-100)."""
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    eos = tokenizer.eos_token or ""
    completion_ids = tokenizer(
        completion + eos, add_special_tokens=False
    )["input_ids"]
    input_ids = prompt_ids + completion_ids
    labels = [-100] * len(prompt_ids) + completion_ids[:]
    if len(input_ids) > max_seq_len:
        input_ids = input_ids[-max_seq_len:]
        labels = labels[-max_seq_len:]
    attention_mask = [1] * len(input_ids)
    return {
        "input_ids": input_ids,
        "labels": labels,
        "attention_mask": attention_mask,
    }


class _SFTDataset:
    def __init__(self, rows: list[dict[str, list[int]]]):
        self.rows = rows

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> dict[str, list[int]]:
        return self.rows[idx]


def _build_collator(pad_id: int):
    import torch

    def collate(batch: list[dict[str, list[int]]]) -> dict[str, "torch.Tensor"]:
        max_len = max(len(b["input_ids"]) for b in batch)
        input_ids, labels, attention_mask = [], [], []
        for b in batch:
            pad_n = max_len - len(b["input_ids"])
            input_ids.append(b["input_ids"] + [pad_id] * pad_n)
            labels.append(b["labels"] + [-100] * pad_n)
            attention_mask.append(b["attention_mask"] + [0] * pad_n)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        }

    return collate


def _evaluate(
    model: Any,
    tokenizer: Any,
    val_samples: list[dict],
    max_new_tokens: int,
    device: str,
) -> dict:
    """Generate completions for val set; score strict verdict+mode accuracy."""
    import torch

    model.eval()
    correct_total = 0
    parse_failures = 0
    verdict_correct = 0
    mode_correct = 0
    per_skill_total: dict[str, int] = defaultdict(int)
    per_skill_correct: dict[str, int] = defaultdict(int)
    per_mode_total: dict[str, int] = defaultdict(int)
    per_mode_correct: dict[str, int] = defaultdict(int)

    for s in val_samples:
        messages = to_messages(s, format_name=NEMOTRON_MINI_4B)
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=1.0,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
        raw = tokenizer.decode(
            out[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )
        expected = s["expected_output"]
        skill = s["skill"]
        mode_gt = s["failure_mode_gt"]
        per_skill_total[skill] += 1
        per_mode_total[mode_gt] += 1
        try:
            parsed = parse_completion(raw, format_name=NEMOTRON_MINI_4B)
        except Exception:
            parse_failures += 1
            continue
        v_ok = parsed.get("verdict") == expected.get("verdict")
        m_ok = parsed.get("failure_mode") == expected.get("failure_mode")
        if v_ok:
            verdict_correct += 1
        if m_ok:
            mode_correct += 1
        if v_ok and m_ok:
            correct_total += 1
            per_skill_correct[skill] += 1
            per_mode_correct[mode_gt] += 1
    n = len(val_samples)
    return {
        "n_val": n,
        "accuracy": correct_total / n if n else 0.0,
        "verdict_accuracy": verdict_correct / n if n else 0.0,
        "failure_mode_accuracy": mode_correct / n if n else 0.0,
        "parse_failures": parse_failures,
        "per_skill_accuracy": {
            k: per_skill_correct[k] / per_skill_total[k] for k in per_skill_total
        },
        "per_failure_mode_accuracy": {
            k: per_mode_correct[k] / per_mode_total[k] for k in per_mode_total
        },
        "per_skill_total": dict(per_skill_total),
        "per_failure_mode_total": dict(per_mode_total),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Cascade C A1 LoRA fine-tune")
    p.add_argument(
        "--model_id", default="nvidia/Nemotron-Mini-4B-Instruct"
    )
    p.add_argument(
        "--dataset",
        type=Path,
        default=THREAD_ROOT.parent / "data/cascade_c_dataset_v0/dataset.jsonl",
    )
    p.add_argument(
        "--output_dir",
        type=Path,
        default=THREAD_ROOT.parent / "data/cascade_c_train_a1_run",
    )
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch_size", type=int, default=8)
    p.add_argument("--grad_accum", type=int, default=2)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--rank", type=int, default=16)
    p.add_argument("--alpha", type=int, default=32)
    p.add_argument("--dropout", type=float, default=0.05)
    p.add_argument("--max_seq_len", type=int, default=1024)
    p.add_argument("--max_new_tokens", type=int, default=256)
    p.add_argument("--val_frac", type=float, default=0.20)
    p.add_argument("--warmup_ratio", type=float, default=0.10)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument(
        "--target_modules",
        default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj",
        help="Comma-separated LoRA target modules; default = all linear",
    )
    args = p.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir = args.output_dir / "ckpt"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    _seed_everything(args.seed)

    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, TaskType
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainerCallback,
        TrainingArguments,
    )

    print(f"[INFO] torch={torch.__version__} cuda={torch.cuda.is_available()}", flush=True)
    print(f"[INFO] device={torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}", flush=True)
    print(f"[INFO] model_id={args.model_id}", flush=True)
    print(f"[INFO] dataset={args.dataset} (exists={args.dataset.exists()})", flush=True)
    print(f"[INFO] output_dir={args.output_dir}", flush=True)

    # ---- dataset
    samples = _load_jsonl(args.dataset)
    print(f"[INFO] loaded {len(samples)} samples", flush=True)
    train_samples, val_samples = _stratified_split(
        samples, val_frac=args.val_frac, seed=args.seed
    )
    print(
        f"[INFO] split train={len(train_samples)} val={len(val_samples)} "
        f"(seed={args.seed}, stratified by skill+mode)",
        flush=True,
    )

    # ---- tokenizer + model
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    pad_id = tokenizer.pad_token_id

    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    model.config.use_cache = False  # required with gradient checkpointing
    model.gradient_checkpointing_enable()
    if hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()

    target_modules = [t.strip() for t in args.target_modules.split(",") if t.strip()]
    peft_cfg = LoraConfig(
        r=args.rank,
        lora_alpha=args.alpha,
        lora_dropout=args.dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=target_modules,
    )
    model = get_peft_model(model, peft_cfg)
    model.print_trainable_parameters()

    # ---- tokenized SFT rows
    def _tokenize(rows: list[dict]) -> list[dict[str, list[int]]]:
        out: list[dict[str, list[int]]] = []
        for s in rows:
            prompt, completion = _build_text_pair(s, tokenizer)
            out.append(
                _tokenize_with_completion_mask(
                    prompt, completion, tokenizer, args.max_seq_len
                )
            )
        return out

    train_rows = _tokenize(train_samples)
    val_rows = _tokenize(val_samples)
    avg_train_len = sum(len(r["input_ids"]) for r in train_rows) / max(1, len(train_rows))
    print(f"[INFO] avg train token len = {avg_train_len:.1f}", flush=True)

    train_ds = Dataset.from_list(train_rows)
    val_ds = Dataset.from_list(val_rows)

    collator = _build_collator(pad_id)

    total_steps = math.ceil(len(train_ds) / (args.batch_size * args.grad_accum)) * args.epochs
    warmup_steps = max(1, int(total_steps * args.warmup_ratio))
    print(f"[INFO] total_steps={total_steps} warmup_steps={warmup_steps}", flush=True)

    training_args = TrainingArguments(
        output_dir=str(ckpt_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=False,  # already enabled on base model
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_steps=warmup_steps,
        weight_decay=0.0,
        bf16=True,
        logging_steps=1,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        report_to=[],
        seed=args.seed,
        data_seed=args.seed,
        remove_unused_columns=False,
    )

    log_history: list[dict] = []

    class _LogCB(TrainerCallback):
        def on_log(self, training_args, state, control, logs=None, **kwargs):
            if logs:
                rec = {"step": state.global_step, **logs}
                log_history.append(rec)
                print(f"[TRAIN] {json.dumps(rec)}", flush=True)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=collator,
        callbacks=[_LogCB()],
    )

    t0 = time.time()
    trainer.train()
    train_elapsed_s = time.time() - t0
    print(f"[INFO] training elapsed = {train_elapsed_s:.1f} s", flush=True)

    # ---- save final LoRA adapter
    model.save_pretrained(ckpt_dir / "final")
    tokenizer.save_pretrained(ckpt_dir / "final")
    print(f"[INFO] saved LoRA adapter to {ckpt_dir / 'final'}", flush=True)

    # ---- strict generation eval on val
    print("[INFO] running strict val eval (generate + parse)…", flush=True)
    device = next(model.parameters()).device
    t1 = time.time()
    metrics = _evaluate(
        model,
        tokenizer,
        val_samples,
        max_new_tokens=args.max_new_tokens,
        device=str(device),
    )
    eval_elapsed_s = time.time() - t1
    print(f"[INFO] strict eval elapsed = {eval_elapsed_s:.1f} s", flush=True)
    print(f"[RESULT] {json.dumps(metrics)}", flush=True)

    summary = {
        "node_id": "T-WM-G2-A1-Train-Run",
        "model_id": args.model_id,
        "dataset_path": str(args.dataset),
        "dataset_total_samples": len(samples),
        "train_n": len(train_samples),
        "val_n": len(val_samples),
        "seed": args.seed,
        "hyperparams": {
            "rank": args.rank,
            "alpha": args.alpha,
            "dropout": args.dropout,
            "target_modules": target_modules,
            "batch_size": args.batch_size,
            "grad_accum": args.grad_accum,
            "lr": args.lr,
            "epochs": args.epochs,
            "max_seq_len": args.max_seq_len,
            "warmup_ratio": args.warmup_ratio,
        },
        "elapsed_s": {
            "training": train_elapsed_s,
            "strict_eval": eval_elapsed_s,
        },
        "log_history": log_history,
        "strict_eval": metrics,
        "phase1_p1_trigger": metrics["accuracy"] >= 0.40,
    }
    metric_path = args.output_dir / "val_metric.json"
    with metric_path.open("w") as f:
        json.dump(summary, f, indent=2)
    print(f"[INFO] wrote {metric_path}", flush=True)

    if metrics["accuracy"] < 0.40:
        print(
            f"[Q6_ABORT_TRIGGER] strict_accuracy={metrics['accuracy']:.4f} < 0.40 "
            "→ Layer 1 FAIL declare + fresh Rs disposition request",
            flush=True,
        )
        return 2
    print(
        f"[P1_TRIGGER] strict_accuracy={metrics['accuracy']:.4f} >= 0.40 "
        "→ Phase 1 P1 grant request packet draft enabled",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
