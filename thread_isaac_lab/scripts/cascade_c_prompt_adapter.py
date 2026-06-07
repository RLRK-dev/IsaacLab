#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Cascade C prompt-format adapter — dataset rows -> chat-template prompts.

Converts T-WM-G2-A0 dataset rows (``data/cascade_c_dataset_v0/dataset.jsonl``,
structured ``input.{obs, log_per_world, extras, context}`` +
``expected_output.{verdict, confidence, failure_mode, recommended_action,
reasoning}``) into HuggingFace-canonical ``messages=[{role, content}, ...]``
plus JSON completion strings, ready for NeMo SFT/LoRA fine-tune
(``T-WM-G2-A1``) and TensorRT-LLM compiled inference (``T-WM-G2-A3``).

Cross-ref:
``thread_isaac_lab/thread-vault/06-Knowledge/LL-Cascade-C-Nemotron-Design.md``
§3 (dataset inheritance) + §1.1 (Nemotron Mini 4B chat-template via tokenizer
``apply_chat_template``).

The adapter is **pure-Python** — it never imports ``transformers``, ``nemo``,
or ``tensorrt_llm`` so the dataset / eval pipelines stay CPU-only and bit-
reproducible without a GPU. Real tokenization happens at A1 fine-tune / A3
inference time via ``tokenizer.apply_chat_template(messages, tokenize=True,
add_generation_prompt=True)`` — that step inserts model-specific special
tokens (``<extra_id_0>System`` etc.) so they are intentionally absent here.

``PROMPT_FORMAT_REGISTRY`` keeps the swap point local: future model swaps
(Qwen2.5-0.5B fallback, NVLM Phase 2, etc.) only need an additional entry,
no callers change.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass

NEMOTRON_MINI_4B = "nemotron_mini_4b"

_NEMOTRON_SYSTEM_PROMPT = (
    "You are a fault classifier for a dual-arm cable manipulation robot "
    "(Franka Panda x2, segmented cable, clip routing). Given one recovery "
    "attempt's observation snapshot (proprioception + per-world telemetry "
    "+ thresholds), classify the outcome into one of "
    "{OK, PRE_FAIL_DETECTED, OOD_HIGH, RECOVERY_PROPOSE} with a failure "
    "mode (F1-F7) and a recovery action JSON. "
    "Reply with one JSON object matching the verdict schema; no prose."
)

_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


# ---------------------------------------------------------------------------
# Format-conversion primitives (Nemotron Mini 4B — ~20 LoC of core logic)
# ---------------------------------------------------------------------------
def _format_user_block(sample: dict) -> str:
    inp = sample["input"]
    ctx = inp["context"]
    return (
        f"Skill: {ctx['skill_name']} (step_id={ctx['step_id']}, "
        f"attempt={ctx['attempt']}/{ctx['max_retry']})\n"
        f"obs: {json.dumps(inp['obs'], separators=(',', ':'))}\n"
        f"log_per_world: {json.dumps(inp['log_per_world'], separators=(',', ':'))}\n"
        f"extras: {json.dumps(inp['extras'], separators=(',', ':'))}\n"
        f"thresholds: {json.dumps(ctx['thresholds'], separators=(',', ':'))}"
    )


def _nemotron_to_messages(sample: dict) -> list[dict]:
    return [
        {"role": "system", "content": _NEMOTRON_SYSTEM_PROMPT},
        {"role": "user", "content": _format_user_block(sample)},
    ]


def _format_completion(sample: dict) -> str:
    return json.dumps(sample["expected_output"], separators=(",", ":"), ensure_ascii=False)


def _to_training_pair(sample: dict) -> dict:
    return {
        "messages": _nemotron_to_messages(sample),
        "completion": _format_completion(sample),
    }


def _parse_completion(raw: str) -> dict:
    """Locate and parse the verdict JSON object inside a raw model completion.

    Handles three observed output shapes:

    * bare JSON (``{"verdict": ...}``)
    * fenced markdown (```` ```json {...} ``` ````)
    * JSON with leading or trailing prose

    Raises ``ValueError`` if no balanced ``{...}`` block is present.
    """
    raw = raw.strip()
    fenced = _FENCED_JSON_RE.search(raw)
    if fenced is not None:
        raw = fenced.group(1)
    start = raw.find("{")
    if start < 0:
        raise ValueError("no JSON object found in completion")
    depth = 0
    for i in range(start, len(raw)):
        ch = raw[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(raw[start : i + 1])
    raise ValueError("unterminated JSON object in completion")


# ---------------------------------------------------------------------------
# Registry — swap point for future models (Qwen0.5B fallback, NVLM Phase 2)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FormatAdapter:
    """Bundle of callables that convert dataset rows for a single LLM family."""

    name: str
    to_messages: Callable[[dict], list[dict]]
    to_training_pair: Callable[[dict], dict]
    format_completion: Callable[[dict], str]
    parse_completion: Callable[[str], dict]


PROMPT_FORMAT_REGISTRY: dict[str, FormatAdapter] = {
    NEMOTRON_MINI_4B: FormatAdapter(
        name=NEMOTRON_MINI_4B,
        to_messages=_nemotron_to_messages,
        to_training_pair=_to_training_pair,
        format_completion=_format_completion,
        parse_completion=_parse_completion,
    ),
}


def get_format(name: str) -> FormatAdapter:
    if name not in PROMPT_FORMAT_REGISTRY:
        raise KeyError(f"unknown prompt format: {name!r}; available: {sorted(PROMPT_FORMAT_REGISTRY)}")
    return PROMPT_FORMAT_REGISTRY[name]


# ---------------------------------------------------------------------------
# Public API (default: Nemotron Mini 4B per Rs gamma disposition 2026-04-29)
# ---------------------------------------------------------------------------
def to_messages(sample: dict, format_name: str = NEMOTRON_MINI_4B) -> list[dict]:
    return get_format(format_name).to_messages(sample)


def to_training_pair(sample: dict, format_name: str = NEMOTRON_MINI_4B) -> dict:
    return get_format(format_name).to_training_pair(sample)


def format_completion(sample: dict, format_name: str = NEMOTRON_MINI_4B) -> str:
    return get_format(format_name).format_completion(sample)


def parse_completion(raw: str, format_name: str = NEMOTRON_MINI_4B) -> dict:
    return get_format(format_name).parse_completion(raw)


__all__ = [
    "NEMOTRON_MINI_4B",
    "FormatAdapter",
    "PROMPT_FORMAT_REGISTRY",
    "format_completion",
    "get_format",
    "parse_completion",
    "to_messages",
    "to_training_pair",
]
