#!/usr/bin/env python3
"""THREAD Architecture Verification Script.

Verifies that all model files are consistent with CLAUDE.md design specifications:
- fusion_dim: 352 (256 visual + 64 proprio + 32 task)
- task_state_dim: 17
- task_latent_dim: 32
- proprio_latent_dim: 64
- visual_latent_dim: 256

Usage:
    python verify_architecture.py
"""

import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class DesignSpec:
    """Design specifications from CLAUDE.md"""
    fusion_dim: int = 352
    visual_latent_dim: int = 256
    proprio_latent_dim: int = 64
    task_latent_dim: int = 32
    task_state_dim: int = 17
    proprio_dim: int = 42
    action_dim: int = 18


@dataclass
class FileCheckResult:
    """Result of checking a single file."""
    file_path: str
    checks: Dict[str, Tuple[bool, str, Optional[int]]]  # key -> (passed, expected, found_value)
    errors: List[str]
    warnings: List[str]


def check_file_for_patterns(file_path: str, spec: DesignSpec) -> FileCheckResult:
    """Check a file for architecture pattern compliance."""
    result = FileCheckResult(
        file_path=file_path,
        checks={},
        errors=[],
        warnings=[]
    )

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        result.errors.append(f"Failed to read file: {e}")
        return result

    # Define patterns to check
    patterns = {
        'fusion_dim': (r'fusion_dim[:\s=]+(\d+)', spec.fusion_dim),
        'task_state_dim': (r'task_state_dim[:\s=]+(\d+)', spec.task_state_dim),
        'task_latent_dim': (r'task_latent_dim[:\s=]+(\d+)', spec.task_latent_dim),
        'proprio_latent_dim': (r'proprio_latent_dim[:\s=]+(\d+)', spec.proprio_latent_dim),
        'visual_latent_dim': (r'visual_latent_dim[:\s=]+(\d+)', spec.visual_latent_dim),
    }

    for name, (pattern, expected) in patterns.items():
        matches = re.findall(pattern, content)
        if matches:
            for match in matches:
                found_value = int(match)
                passed = found_value == expected
                result.checks[name] = (passed, str(expected), found_value)
                if not passed:
                    result.errors.append(
                        f"{name}: expected {expected}, found {found_value}"
                    )

    # Check for old 256D fusion_dim (common error)
    if 'fusion_dim' not in result.checks:
        old_fusion_match = re.search(r'fusion_dim[:\s=]+256\b', content)
        if old_fusion_match:
            result.checks['fusion_dim'] = (False, '352', 256)
            result.errors.append("fusion_dim: found old value 256, should be 352")

    # Check for task_state in forward method signature
    if 'def forward' in content:
        # Check if forward accepts task_state
        forward_match = re.search(r'def forward\([^)]+\)', content, re.DOTALL)
        if forward_match:
            forward_sig = forward_match.group(0)
            if 'task_state' not in forward_sig and 'WorldModel' in file_path:
                result.warnings.append("forward() may be missing task_state parameter")

    return result


def find_model_files(base_path: str) -> List[str]:
    """Find all relevant model files to check."""
    files = []

    # Key files to check
    key_paths = [
        'thread_isaac_lab/models/base_policy.py',
        'thread_isaac_lab/models/skill_adapter.py',
        'thread_isaac_lab/models/skill_adapter_with_prediction.py',
        'thread_isaac_lab/models/goal_conditioned_adapter.py',
        'thread_isaac_lab/models/world_model_with_task.py',
        'thread_isaac_lab/scripts/train_dual_arm_msa.py',
        'thread_isaac_lab/scripts/train_dual_arm_wm.py',
        'thread_isaac_lab/scripts/train_base_policy.py',
        'thread_isaac_lab/scripts/train_skill_adapter.py',
        'thread_isaac_lab/scripts/train_skill_adapter_v2.py',
    ]

    for rel_path in key_paths:
        full_path = os.path.join(base_path, rel_path)
        if os.path.exists(full_path):
            files.append(full_path)

    return files


def print_report(results: List[FileCheckResult], spec: DesignSpec):
    """Print verification report."""
    print("=" * 70)
    print("THREAD Architecture Verification Report")
    print("=" * 70)
    print()

    # Print design specs
    print("Design Specifications (from CLAUDE.md):")
    print(f"  fusion_dim:        {spec.fusion_dim} (256 visual + 64 proprio + 32 task)")
    print(f"  visual_latent_dim: {spec.visual_latent_dim}")
    print(f"  proprio_latent_dim:{spec.proprio_latent_dim}")
    print(f"  task_latent_dim:   {spec.task_latent_dim}")
    print(f"  task_state_dim:    {spec.task_state_dim}")
    print()

    total_errors = 0
    total_warnings = 0

    # Print per-file results
    for result in results:
        rel_path = os.path.relpath(result.file_path)
        has_issues = result.errors or result.warnings

        if has_issues:
            print(f"[{'FAIL' if result.errors else 'WARN'}] {rel_path}")
        else:
            print(f"[PASS] {rel_path}")

        # Print checks
        for name, (passed, expected, found) in result.checks.items():
            status = "✓" if passed else "✗"
            print(f"       {status} {name}: {found} (expected: {expected})")

        # Print errors
        for error in result.errors:
            print(f"       ERROR: {error}")
            total_errors += 1

        # Print warnings
        for warning in result.warnings:
            print(f"       WARN: {warning}")
            total_warnings += 1

        print()

    # Print summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    passed_files = sum(1 for r in results if not r.errors)
    print(f"  Files checked:  {len(results)}")
    print(f"  Files passed:   {passed_files}")
    print(f"  Files failed:   {len(results) - passed_files}")
    print(f"  Total errors:   {total_errors}")
    print(f"  Total warnings: {total_warnings}")
    print()

    if total_errors == 0:
        print("✓ All files are consistent with CLAUDE.md design specifications!")
        return 0
    else:
        print("✗ Some files have inconsistencies. Please review and fix.")
        return 1


def main():
    """Main entry point."""
    # Determine base path
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent  # IsaacLab/

    print(f"Base path: {base_path}")
    print()

    # Load design spec
    spec = DesignSpec()

    # Find files to check
    files = find_model_files(str(base_path))

    if not files:
        print("No model files found to check!")
        return 1

    print(f"Found {len(files)} files to check:")
    for f in files:
        print(f"  - {os.path.relpath(f, base_path)}")
    print()

    # Check each file
    results = []
    for file_path in files:
        result = check_file_for_patterns(file_path, spec)
        results.append(result)

    # Print report
    exit_code = print_report(results, spec)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
