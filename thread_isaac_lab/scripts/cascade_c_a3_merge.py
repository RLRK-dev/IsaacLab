#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Cascade C A3.1 — merge LoRA adapter into Nemotron Mini 4B base.

Reads LoRA adapter from ``data/cascade_c_train_a1_run/ckpt/final/`` and
merges into ``nvidia/Nemotron-Mini-4B-Instruct`` base model via
``peft.PeftModel.merge_and_unload()``. Saves merged FP16 model to
``data/cascade_c_a3_build/merged_fp16/``.

Output is a single deployable model directory (no LoRA wrapper needed at
inference time). Subsequent A3 steps quantize this merged model to INT4
via onnxruntime_genai model_builder + export to ONNX for ORT-GenAI
inference.

Bounds: TOUCH FORBIDDEN strict (env / task_config.py / scripted_skills /
step_table / existing cascade_c_*.py / routing_orchestrator / existing
tests / CLAUDE.md / prohibited.md / AGENTS.md / env_isaaclab UNCHANGED).
New files only under data/cascade_c_a3_build/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--adapter_dir",
        default="data/cascade_c_train_a1_run/ckpt/final",
        help="LoRA adapter directory",
    )
    parser.add_argument(
        "--base_model",
        default="nvidia/Nemotron-Mini-4B-Instruct",
        help="HF base model id",
    )
    parser.add_argument(
        "--output_dir",
        default="data/cascade_c_a3_build/merged_fp16",
        help="Output merged FP16 model directory",
    )
    args = parser.parse_args()

    adapter_dir = Path(args.adapter_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not adapter_dir.is_dir():
        print(f"ERROR: adapter_dir does not exist: {adapter_dir}", file=sys.stderr)
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[merge] adapter_dir = {adapter_dir}")
    print(f"[merge] base_model = {args.base_model}")
    print(f"[merge] output_dir = {output_dir}")

    print("[merge] importing torch + transformers + peft...")
    t0 = time.time()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"[merge] torch {torch.__version__} cuda={torch.cuda.is_available()}")

    print(f"[merge] loading base model ({args.base_model}) in bf16...")
    t1 = time.time()
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        dtype=torch.bfloat16,
        device_map="cpu",
        trust_remote_code=False,
    )
    print(f"[merge] base loaded in {time.time() - t1:.1f}s")

    print(f"[merge] loading LoRA adapter from {adapter_dir}...")
    t2 = time.time()
    peft_model = PeftModel.from_pretrained(base, str(adapter_dir))
    print(f"[merge] adapter loaded in {time.time() - t2:.1f}s")

    print("[merge] merging LoRA into base via merge_and_unload()...")
    t3 = time.time()
    merged = peft_model.merge_and_unload()
    print(f"[merge] merged in {time.time() - t3:.1f}s")

    print(f"[merge] saving merged FP16 model to {output_dir}...")
    t4 = time.time()
    merged.save_pretrained(str(output_dir), safe_serialization=True)
    print(f"[merge] save complete in {time.time() - t4:.1f}s")

    print(f"[merge] copying tokenizer from {args.base_model}...")
    t5 = time.time()
    tok = AutoTokenizer.from_pretrained(args.base_model)
    tok.save_pretrained(str(output_dir))
    print(f"[merge] tokenizer saved in {time.time() - t5:.1f}s")

    # SHA-256 pin top-level safetensors files
    print("[merge] computing SHA-256 of output files...")
    sha_map: dict[str, str] = {}
    for f in sorted(output_dir.rglob("*")):
        if f.is_file() and f.suffix in {".safetensors", ".json", ".model", ".bin"}:
            rel = str(f.relative_to(output_dir))
            sha_map[rel] = sha256_file(f)
            print(f"  {rel}: {sha_map[rel][:16]}... ({f.stat().st_size / 1e6:.1f} MB)")

    sha_path = output_dir / "merge_sha256.json"
    sha_path.write_text(json.dumps(sha_map, indent=2, sort_keys=True))
    print(f"[merge] SHA-256 manifest written to {sha_path}")

    elapsed = time.time() - t0
    print(f"[merge] DONE in {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
