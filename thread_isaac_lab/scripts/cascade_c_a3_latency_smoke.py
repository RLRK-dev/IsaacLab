#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Cascade C A3.4 — ONNX INT4 latency smoke test (cuda EP).

Loads the ONNX INT4 model from ``data/cascade_c_a3_build/onnx_int4/`` via
``onnxruntime_genai`` (cuda EP) and measures end-to-end inference latency
on Cascade C validation samples. Reports p50/p95/p99 against the A3
design ceiling (p95 <= 100 ms).

The latency target reflects the inline retry decision budget the
classifier must stay under for in-loop deployment. Smoke runs do not
constitute Gate 2 acceptance evidence — that is A6-Bench scope.

Bounds: TOUCH FORBIDDEN strict (env / task_config.py / scripted_skills /
step_table / existing cascade_c_*.py / routing_orchestrator / existing
tests / CLAUDE.md / prohibited.md / AGENTS.md / env_isaaclab UNCHANGED).
Reads existing dataset.jsonl + prompt_adapter; emits new artifacts only
under data/cascade_c_a3_build/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def load_val_samples(
    dataset_path: Path, prompt_adapter_module, n: int, seed: int = 0
) -> list[dict]:
    """Pick `n` samples from dataset.jsonl (same stratified-by-skill seed as A1)."""
    import random

    rng = random.Random(seed)
    records: list[dict] = []
    with dataset_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    rng.shuffle(records)
    return records[:n]


def build_prompt_messages(sample: dict, adapter_module) -> list[dict]:
    """Return the adapter's messages list (role/content) for chat template."""
    pair = adapter_module.to_training_pair(sample)
    return pair["messages"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_dir",
        default="data/cascade_c_a3_build/onnx_int4",
        help="ONNX INT4 model directory (onnxruntime_genai compatible)",
    )
    parser.add_argument(
        "--dataset",
        default="data/cascade_c_dataset_v0/dataset.jsonl",
        help="Cascade C dataset for sample prompts",
    )
    parser.add_argument(
        "--n_samples",
        type=int,
        default=100,
        help="Number of unique prompts to evaluate",
    )
    parser.add_argument(
        "--n_trials",
        type=int,
        default=10,
        help="Number of trials per sample (latency stat power)",
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=192,
        help="Cap on generation length per call",
    )
    parser.add_argument(
        "--warmup_calls",
        type=int,
        default=5,
        help="Discard the first N latency samples to settle CUDA JIT",
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="Sample selection seed"
    )
    parser.add_argument(
        "--output",
        default="data/cascade_c_a3_build/latency_smoke.json",
        help="Output JSON file",
    )
    parser.add_argument(
        "--target_p95_ms",
        type=float,
        default=100.0,
        help="Target latency p95 ceiling in ms (per A3-Design §6)",
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir).resolve()
    dataset_path = Path(args.dataset).resolve()
    output_path = Path(args.output).resolve()

    if not model_dir.is_dir():
        print(f"ERROR: model_dir not found: {model_dir}", file=sys.stderr)
        return 1
    if not dataset_path.is_file():
        print(f"ERROR: dataset not found: {dataset_path}", file=sys.stderr)
        return 1

    print(f"[smoke] model_dir = {model_dir}")
    print(f"[smoke] dataset = {dataset_path}")
    print(f"[smoke] n_samples = {args.n_samples}, n_trials = {args.n_trials}")
    print(f"[smoke] max_new_tokens = {args.max_new_tokens}")

    # Import prompt adapter via sys.path push so we exercise the SAME adapter
    # that A1 trained against (SHA pinned).
    print("[smoke] importing cascade_c_prompt_adapter...")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import cascade_c_prompt_adapter as adapter_module

    print("[smoke] importing onnxruntime_genai...")
    import onnxruntime_genai as og

    print(f"[smoke] onnxruntime_genai version: {og.__version__}")

    print("[smoke] loading samples...")
    samples = load_val_samples(dataset_path, adapter_module, args.n_samples, args.seed)
    if len(samples) < args.n_samples:
        print(
            f"WARNING: requested {args.n_samples} samples, dataset only "
            f"has {len(samples)}; truncating.",
            file=sys.stderr,
        )

    print("[smoke] precomputing messages...")
    all_messages = [build_prompt_messages(s, adapter_module) for s in samples]

    print(f"[smoke] loading ONNX model from {model_dir}...")
    t_load = time.time()
    model = og.Model(str(model_dir))
    print(f"[smoke] og model loaded in {time.time() - t_load:.1f}s")

    print("[smoke] loading HF tokenizer (og.Tokenizer not supported for this model)...")
    from transformers import AutoTokenizer

    t_tok = time.time()
    hf_tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    print(f"[smoke] HF tokenizer loaded in {time.time() - t_tok:.1f}s")

    # Pre-encode all prompts once to isolate inference latency.
    # Use apply_chat_template to match training format (chat markers + assistant
    # generation prompt) so the model knows where its response ends (EOS).
    print("[smoke] tokenizing prompts via apply_chat_template...")
    token_seqs = []
    prompt_strs = []
    for msgs in all_messages:
        prompt = hf_tokenizer.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=False
        )
        prompt_strs.append(prompt)
        toks = hf_tokenizer.encode(prompt, add_special_tokens=False)
        token_seqs.append(toks)
    token_lens = [len(t) for t in token_seqs]
    prompt_char_lens = [len(p) for p in prompt_strs]
    print(
        f"[smoke] prompt char lens: min={min(prompt_char_lens)}, "
        f"mean={sum(prompt_char_lens) / len(prompt_char_lens):.0f}, "
        f"max={max(prompt_char_lens)}"
    )
    print(
        f"[smoke] token lens: min={min(token_lens)}, "
        f"mean={sum(token_lens) / len(token_lens):.0f}, max={max(token_lens)}"
    )

    print("[smoke] starting smoke trials...")
    latencies_ms: list[float] = []
    output_tokens_per_call: list[int] = []
    t_run = time.time()

    for trial in range(args.n_trials):
        for i, toks in enumerate(token_seqs):
            params = og.GeneratorParams(model)
            params.set_search_options(
                max_length=len(toks) + args.max_new_tokens,
                do_sample=False,
                temperature=1.0,
            )

            t0 = time.perf_counter()
            gen = og.Generator(model, params)
            gen.append_tokens(toks)
            n_out = 0
            while not gen.is_done():
                gen.generate_next_token()
                n_out += 1
                if n_out >= args.max_new_tokens:
                    break
            t1 = time.perf_counter()

            latencies_ms.append((t1 - t0) * 1000.0)
            output_tokens_per_call.append(n_out)

            del gen
            del params

    elapsed = time.time() - t_run
    print(f"[smoke] trials complete in {elapsed:.1f}s")

    # Drop warmup
    if len(latencies_ms) <= args.warmup_calls:
        print(
            f"WARNING: warmup_calls={args.warmup_calls} >= total samples; "
            "no measurement window left.",
            file=sys.stderr,
        )
        return 2
    measured = latencies_ms[args.warmup_calls :]
    out_tok = output_tokens_per_call[args.warmup_calls :]

    p50 = statistics.median(measured)
    p95 = statistics.quantiles(measured, n=20)[18]  # 95th percentile (20-quantile)
    p99 = statistics.quantiles(measured, n=100)[98]  # 99th percentile
    pmax = max(measured)
    pmin = min(measured)
    pmean = statistics.mean(measured)

    tok_mean = statistics.mean(out_tok)
    tok_median = statistics.median(out_tok)
    tok_max = max(out_tok)

    print()
    print("=" * 60)
    print("LATENCY SMOKE RESULT")
    print("=" * 60)
    print(f"  total measurements: {len(measured)} (after dropping {args.warmup_calls} warmup)")
    print(f"  output tokens/call: mean={tok_mean:.1f}, median={tok_median}, max={tok_max}")
    print(f"  latency_min_ms:    {pmin:.1f}")
    print(f"  latency_p50_ms:    {p50:.1f}")
    print(f"  latency_mean_ms:   {pmean:.1f}")
    print(f"  latency_p95_ms:    {p95:.1f}   (target {args.target_p95_ms:.1f})")
    print(f"  latency_p99_ms:    {p99:.1f}")
    print(f"  latency_max_ms:    {pmax:.1f}")
    print()
    target_pass = p95 <= args.target_p95_ms
    print(f"  p95 ceiling PASS:  {target_pass}")

    # SHA-pin output artifacts
    sha_map: dict[str, str] = {}
    for f in sorted(model_dir.iterdir()):
        if f.is_file():
            sha_map[f.name] = sha256_file(f)

    payload = {
        "node_id": "T-WM-G2-A3-Build-Run",
        "step": "A3.4_latency_smoke",
        "model_dir": str(model_dir),
        "dataset": str(dataset_path),
        "n_samples": len(samples),
        "n_trials": args.n_trials,
        "max_new_tokens": args.max_new_tokens,
        "warmup_calls": args.warmup_calls,
        "target_p95_ms": args.target_p95_ms,
        "result": {
            "latency_ms": {
                "min": pmin,
                "p50": p50,
                "mean": pmean,
                "p95": p95,
                "p99": p99,
                "max": pmax,
            },
            "output_tokens_per_call": {
                "mean": tok_mean,
                "median": tok_median,
                "max": tok_max,
            },
            "n_measurements": len(measured),
            "p95_pass": target_pass,
        },
        "engine_artifact_sha256": sha_map,
        "elapsed_s": elapsed,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))
    print(f"[smoke] result written to {output_path}")
    return 0 if target_pass else 3


if __name__ == "__main__":
    sys.exit(main())
