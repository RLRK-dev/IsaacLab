#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Cluster G floor preservation git-diff binary check helper.

Implements hook_spec.md §3 master §5.1 7-file canonical + line-range gate
(File #2 execute_step L1040-L1075 / File #3 _rollback L1103-L1153).

Exit codes (matches hook_spec.md §5.4 + dispatcher contract):
  0 = PASS
  1 = FAIL_GIT_DIFF (master §5.1 7-file unchanged violation)
  2 = FAIL_TEST    (Cluster G existing test FAIL — handled by dispatcher)
  3 = FAIL_SR      (per-skill SR threshold violation — handled by monitor)
  4 = FAIL_INFRA   (git binary not found / Python ImportError / disk full)

Output: structured JSON to --output-json path matching hook_spec.md §4 schema.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

EXIT_PASS = 0
EXIT_FAIL_GIT_DIFF = 1
EXIT_FAIL_TEST = 2
EXIT_FAIL_SR = 3
EXIT_FAIL_INFRA = 4

# hook_spec.md §3 master §5.1 7-file canonical (Cluster G floor preservation contract).
# File #1/#4/#5/#6/#7 = binary unchanged (0 lines diff).
# File #2 = L1040-L1075 range only allowed (execute_step L1050 hook injection slot ±25).
# File #3 = L1103-L1153 range only allowed (_rollback bc_p0_region_check extension ~10 LoC).
ORCHESTRATOR_PATH = "thread_isaac_lab/orchestrator/routing_orchestrator.py"
MASTER_FILES_BINARY_UNCHANGED = [
    # File #1: execute_skill (L862-899) — embedded in routing_orchestrator.py file #2/#3 share
    # Tracked at file-level via line-range gates; this list is the binary (0-diff) set.
    "thread_isaac_lab/skills/result.py",
    "thread_isaac_lab/skills/snapshot.py",
    "thread_isaac_lab/skills/scripted_skills.py",
    "thread_isaac_lab/skills/step_table.py",
]
ALLOWED_DIFF_RANGES = {
    # File #2: execute_step L1040-L1075 hook injection slot.
    f"{ORCHESTRATOR_PATH}:execute_step": (1040, 1075),
    # File #3: _rollback L1103-L1153 bc_p0_region_check extension.
    f"{ORCHESTRATOR_PATH}:_rollback": (1103, 1153),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cluster G floor preservation git-diff audit helper.")
    parser.add_argument("--baseline-sha", required=True, help="Production baseline SHA")
    parser.add_argument("--head-sha", required=True, help="HEAD SHA to verify")
    parser.add_argument("--audit-id", default=None, help="Audit ID UUID (auto-generated if absent)")
    parser.add_argument("--ts", default=None, help="ISO 8601 timestamp (auto if absent)")
    parser.add_argument(
        "--stage",
        required=True,
        choices=["pre-deploy", "pre-canary", "per-canary-stage", "steady-state"],
        help="Audit stage name",
    )
    parser.add_argument("--output-json", required=True, type=Path, help="Structured JSON output path")
    parser.add_argument("--repo-root", default=".", help="Repo root for git invocation")
    parser.add_argument(
        "--diff-text-file",
        type=Path,
        default=None,
        help="Read pre-canned diff text from this file instead of running git (testing only)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Skip subprocess git calls; emit canned PASS payload")
    return parser.parse_args()


def run_git_diff(repo_root: str, baseline: str, head: str) -> tuple[int, str]:
    """Return (returncode, stdout). Negative rc reserved for infra errors."""
    try:
        sha_check = subprocess.run(
            ["git", "-C", repo_root, "cat-file", "-e", baseline],
            capture_output=True, text=True, check=False, timeout=10,
        )
    except FileNotFoundError:
        return -1, "git binary not found"
    except subprocess.TimeoutExpired:
        return -1, "git cat-file timed out"
    if sha_check.returncode != 0:
        return -1, f"baseline SHA not in repo: {baseline}"
    cmd = [
        "git", "-C", repo_root, "diff", f"{baseline}..{head}", "--",
        ORCHESTRATOR_PATH,
        *MASTER_FILES_BINARY_UNCHANGED,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    except FileNotFoundError:
        return -1, "git binary not found"
    except subprocess.TimeoutExpired:
        return -1, "git diff timed out"
    if r.returncode != 0:
        return -1, f"git diff exit {r.returncode}: {r.stderr.strip()}"
    return 0, r.stdout


def parse_diff_violations(diff_text: str) -> tuple[list[str], dict[str, list[tuple[int, int]]]]:
    """Return (violation_files, allowed_diff_line_ranges_per_file).

    Violation = file in MASTER_FILES_BINARY_UNCHANGED with any non-zero hunk,
    OR routing_orchestrator.py hunk outside ALLOWED_DIFF_RANGES.
    """
    violations: list[str] = []
    per_file_hunks: dict[str, list[tuple[int, int]]] = {}
    current_file: str | None = None
    hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            # `diff --git a/<path> b/<path>` — keep b-side path
            parts = line.split()
            current_file = parts[3][2:] if len(parts) >= 4 else None
            per_file_hunks.setdefault(current_file or "", [])
            continue
        m = hunk_re.match(line)
        if m and current_file:
            start = int(m.group(1))
            count = int(m.group(2)) if m.group(2) else 1
            per_file_hunks[current_file].append((start, start + max(count - 1, 0)))

    for f in MASTER_FILES_BINARY_UNCHANGED:
        if per_file_hunks.get(f):
            violations.append(f)

    if ORCHESTRATOR_PATH in per_file_hunks:
        for start, end in per_file_hunks[ORCHESTRATOR_PATH]:
            in_any_allowed = any(
                lo <= start and end <= hi for (lo, hi) in ALLOWED_DIFF_RANGES.values()
            )
            if not in_any_allowed:
                violations.append(f"{ORCHESTRATOR_PATH}:L{start}-L{end}")
    return violations, per_file_hunks


def build_payload(
    stage: str, ts: str, audit_id: str, baseline: str, head: str,
    violations: list[str], hunks: dict[str, list[tuple[int, int]]],
    git_diff_pass: bool,
) -> dict:
    verdict = "PASS" if git_diff_pass else "FAIL"
    return {
        "stage": stage,
        "ts": ts,
        "audit_id": audit_id,
        "git_diff": {
            "production_sha": baseline,
            "head_sha": head,
            "violation_files": violations,
            "allowed_diff_lines": {f: hunks.get(f, []) for f in [ORCHESTRATOR_PATH]},
            "verdict": verdict,
        },
        "cluster_g_test": {"tests_run": 0, "tests_passed": 0, "tests_failed": 0, "verdict": "SKIP"},
        "per_skill_sr": {"verdict": "SKIP"},
        "overall_verdict": verdict,
        "exit_code": EXIT_PASS if git_diff_pass else EXIT_FAIL_GIT_DIFF,
        "alarm_action": "NONE" if git_diff_pass else ("RC4" if stage in ("pre-deploy", "per-canary-stage", "steady-state") else "RP3"),
    }


def main() -> int:
    args = parse_args()
    audit_id = args.audit_id or str(uuid.uuid4())
    ts = args.ts or datetime.now(timezone.utc).isoformat()

    if args.dry_run:
        payload = build_payload(args.stage, ts, audit_id, args.baseline_sha, args.head_sha, [], {}, True)
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, indent=2))
        print(f"[DRY-RUN PASS] {args.stage} audit_id={audit_id}")
        return EXIT_PASS

    if args.diff_text_file is not None:
        if not args.diff_text_file.exists():
            print(f"[FAIL_INFRA] diff-text-file not found: {args.diff_text_file}", file=sys.stderr)
            return EXIT_FAIL_INFRA
        rc, stdout = 0, args.diff_text_file.read_text()
    else:
        rc, stdout = run_git_diff(args.repo_root, args.baseline_sha, args.head_sha)
    if rc < 0:
        payload = build_payload(args.stage, ts, audit_id, args.baseline_sha, args.head_sha, ["__infra__"], {}, False)
        payload["exit_code"] = EXIT_FAIL_INFRA
        payload["overall_verdict"] = "FAIL"
        payload["alarm_action"] = "RC4"
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, indent=2))
        print(f"[FAIL_INFRA] {stdout}", file=sys.stderr)
        return EXIT_FAIL_INFRA

    violations, hunks = parse_diff_violations(stdout)
    git_diff_pass = not violations
    payload = build_payload(args.stage, ts, audit_id, args.baseline_sha, args.head_sha, violations, hunks, git_diff_pass)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2))
    if git_diff_pass:
        print(f"[PASS] {args.stage} Cluster G floor unchanged audit_id={audit_id}")
        return EXIT_PASS
    print(f"[FAIL_GIT_DIFF] master §5.1 violation: {violations}", file=sys.stderr)
    return EXIT_FAIL_GIT_DIFF


if __name__ == "__main__":
    sys.exit(main())
