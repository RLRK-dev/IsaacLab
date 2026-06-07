#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""RobotTAS v1 mini CLI.

Lightweight CLI for editing a single UI-owned field of
``data/waypoints/full_43step.json`` and validating the edit via the
``robottas_v1_ik_wrapper`` backend. No GUI, no ViewerGL; intended for
SSH/headless workflows and as the Phase 1b foundation in the phased
path (see ``09-RobotTAS-v1/DEFINE.md`` v1 round 3).

See ``09-RobotTAS-v1/api-contract.md`` §3 for the full CLI contract.

Usage::

    python thread_isaac_lab/scripts/robottas_mini.py \\
        --step 5 --field target_l.z --delta 0.01 --device cuda:0

Exit codes:
    0  edit applied + IK validate PASS (43/43)
    1  edit applied + IK validate FAIL (any STEP)
    2  user aborted (Ctrl+C or [n] at confirm)
    3  ValueError (field whitelist, step range, delta out-of-range)
    4  FileNotFoundError (JSON path missing)
    5  subprocess timeout
    6  subprocess killed
   99  internal exception
"""

from __future__ import annotations

import argparse
import copy
import datetime
import json
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from robottas_v1_ik_wrapper import (  # noqa: E402
    ALLOWED_DEVICES,
    ALLOWED_EDIT_FIELDS,
    VALID_JSON_DIR,
    append_usage_log,
    atomic_write_json,
    create_backup,
    invoke_dry_run,
    now_jst_iso,
    validate_edit_field,
)

VERSION_TAG = "v1_round_3"
FRONTEND_TAG = "mini"
FINGER_MIN = 0.002
FINGER_MAX = 0.04
TARGET_RANGE = (-1.5, 1.5)  # m, sanity clip on absolute target_l/r value


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="robottas_mini",
        description="RobotTAS v1 mini CLI: single-field waypoint edit + IK validate.",
    )
    p.add_argument("--step", type=int, required=True, help="STEP index (1-43)")
    p.add_argument(
        "--field",
        required=True,
        help=f"UI-owned field. Allowed: {sorted(ALLOWED_EDIT_FIELDS)}",
    )
    p.add_argument("--delta", type=float, required=True, help="Signed delta in meters")
    p.add_argument(
        "--device",
        required=True,
        choices=sorted(ALLOWED_DEVICES),
        help="cuda:0 / cuda:1 / cuda:2",
    )
    p.add_argument(
        "--json-path",
        type=Path,
        default=VALID_JSON_DIR / "full_43step.json",
        help="Override waypoint JSON path (default: full_43step.json)",
    )
    p.add_argument("--dry", action="store_true", help="Dry-run: preview only, no write")
    p.add_argument("--no-confirm", action="store_true", help="Skip [y/N] confirm prompt")
    p.add_argument("--timeout", type=int, default=60, help="Subprocess timeout seconds")
    return p.parse_args(argv)


def _err(msg: str) -> None:
    print(f"[robottas_mini] ERROR: {msg}", file=sys.stderr)


def _info(msg: str) -> None:
    print(f"[robottas_mini] {msg}")


def _validate_range(field_name: str, old_val: float, new_val: float) -> None:
    if field_name in ("left_finger", "right_finger"):
        if not (FINGER_MIN <= new_val <= FINGER_MAX):
            raise ValueError(f"{field_name} new value {new_val:.4f} outside [{FINGER_MIN}, {FINGER_MAX}] m")
    else:  # target_l / target_r component
        lo, hi = TARGET_RANGE
        if not (lo <= new_val <= hi):
            raise ValueError(f"{field_name} new value {new_val:.4f} outside sanity range [{lo}, {hi}] m")


def _apply_edit(data: dict, step: int, field: str, delta: float) -> tuple[dict, dict, dict]:
    """Apply the edit to an in-memory copy, returning (before, after, field_info)."""
    if not 1 <= step <= 43:
        raise ValueError(f"step {step} out of range [1, 43]")
    field_name, idx = validate_edit_field(field)
    new_data = copy.deepcopy(data)
    step_dict = new_data["steps"][step - 1]
    if idx >= 0:
        before = dict(step_dict)
        old_val = float(step_dict[field_name][idx])
        new_val = old_val + delta
        _validate_range(f"{field_name}.{'xyz'[idx]}", old_val, new_val)
        step_dict[field_name][idx] = new_val
        after = dict(step_dict)
    else:
        before = dict(step_dict)
        old_val = float(step_dict[field_name])
        new_val = old_val + delta
        _validate_range(field_name, old_val, new_val)
        step_dict[field_name] = new_val
        after = dict(step_dict)
    return new_data, before, after


def _print_diff(step: int, field: str, before: dict, after: dict) -> None:
    field_name, idx = validate_edit_field(field)
    if idx >= 0:
        _info(f"STEP {step} {field}")
        comp = "xyz"[idx]
        bl = before[field_name]
        al = after[field_name]
        print(f"  Before: ({bl[0]:.4f}, {bl[1]:.4f}, {bl[2]:.4f})")
        print(f"  After:  ({al[0]:.4f}, {al[1]:.4f}, {al[2]:.4f})  [{comp} delta]")
    else:
        _info(f"STEP {step} {field_name}")
        print(f"  Before: {before[field_name]:.4f}")
        print(f"  After:  {after[field_name]:.4f}")


def _confirm() -> bool:
    try:
        ans = input("Apply edit? [y/N]: ").strip().lower()
    except EOFError:
        return False
    return ans in {"y", "yes"}


class _Spinner:
    """Minimal 1Hz stdout spinner for non-blocking subprocess invoke."""

    _CHARS = "|/-\\"

    def __init__(self, label: str = "") -> None:
        self.label = label
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)
        # Clear line.
        sys.stdout.write("\r" + " " * 72 + "\r")
        sys.stdout.flush()

    def _run(self) -> None:
        i = 0
        t0 = time.monotonic()
        while not self._stop.is_set():
            elapsed = time.monotonic() - t0
            ch = self._CHARS[i % len(self._CHARS)]
            sys.stdout.write(f"\r[robottas_mini] {self.label} {ch}  ({elapsed:.1f}s)")
            sys.stdout.flush()
            i += 1
            self._stop.wait(1.0)


def _extract_err(step_dict: dict) -> dict:
    return {
        "l_mm": float(step_dict.get("err_l_mm", 0.0)),
        "r_mm": float(step_dict.get("err_r_mm", 0.0)),
    }


def _status_of(step_dict: dict) -> str:
    return str(step_dict.get("status", "UNKNOWN"))


def _make_session_id() -> str:
    return f"robottas_mini_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
    except SystemExit as exc:
        return 3 if exc.code not in (0, None) else int(exc.code or 0)
    session_id = _make_session_id()

    json_path: Path = args.json_path
    try:
        json_path = json_path.resolve()
    except OSError:
        _err(f"invalid --json-path: {json_path}")
        return 4
    if not json_path.is_file():
        _err(f"JSON not found: {json_path}")
        return 4

    try:
        with open(json_path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        _err(f"failed to load JSON: {exc}")
        return 99

    try:
        new_data, before, after = _apply_edit(data, args.step, args.field, args.delta)
    except ValueError as exc:
        _err(str(exc))
        return 3

    _print_diff(args.step, args.field, before, after)

    err_before = _extract_err(before)
    status_before = _status_of(before)

    if args.dry:
        _info("[dry] preview only, no write. usage-log skipped.")
        return 0

    if not args.no_confirm and not _confirm():
        _info("aborted by user.")
        return 2

    # Backup (skip-create preserves oldest baseline).
    try:
        backup_path = create_backup(json_path, skip_if_exists=True)
        if backup_path is None:
            _info("backup: skipped (oldest baseline preserved)")
        else:
            _info(f"backup: {backup_path}")
    except (OSError, ValueError) as exc:
        _err(f"backup failed: {exc}")
        return 99

    # Atomic write of edited JSON.
    try:
        atomic_write_json(json_path, new_data)
    except OSError as exc:
        _err(f"atomic_write_json failed: {exc}")
        return 99

    # Invoke subprocess with progress indicator.
    spinner = _Spinner(label="Invoking dry_run_43step.py")
    spinner.start()
    t0 = time.monotonic()
    try:
        result = invoke_dry_run(json_path, args.device, timeout_s=args.timeout)
    except KeyboardInterrupt:
        spinner.stop()
        _info("interrupted by user during subprocess invoke.")
        return 6
    except (ValueError, FileNotFoundError) as exc:
        spinner.stop()
        _err(f"invoke_dry_run failed: {exc}")
        return 99
    finally:
        spinner.stop()
    wall = time.monotonic() - t0

    if result.timed_out:
        _err(f"subprocess timed out after {args.timeout}s (wall {wall:.1f}s)")
        exit_code = 5
    elif result.killed:
        _err("subprocess killed")
        exit_code = 6
    else:
        _info(f"Completed in {result.duration_seconds:.1f}s (returncode={result.returncode})")
        exit_code = int(result.returncode) if result.returncode in (0, 1) else 99

    # Display updated STEP details if the subprocess succeeded in writing back.
    err_after: dict | None = None
    status_after: str = "UNKNOWN"
    if result.updated_steps is not None:
        try:
            new_step = result.updated_steps[args.step - 1]
            err_after = _extract_err(new_step)
            status_after = _status_of(new_step)
            _info(f"STEP {args.step} IK result:")
            print(f"  err_l_mm: {err_before['l_mm']:.2f} -> {err_after['l_mm']:.2f}")
            print(f"  err_r_mm: {err_before['r_mm']:.2f} -> {err_after['r_mm']:.2f}")
            print(f"  status:   {status_before} -> {status_after}")
        except (IndexError, KeyError):
            pass

    # Usage-log append (even for FAIL/timeout/killed to provide evidence).
    try:
        append_usage_log(
            {
                "timestamp": now_jst_iso(),
                "user": os.environ.get("USER") or "unknown",
                "session_id": session_id,
                "edited_step": args.step,
                "edited_field": args.field,
                "delta": args.delta,
                "err_before": err_before,
                "err_after": err_after,
                "duration_seconds": result.duration_seconds,
                "subprocess_returncode": int(result.returncode),
                "status_transition": f"{status_before}->{status_after}",
                "frontend": FRONTEND_TAG,
                "version": VERSION_TAG,
                "timed_out": result.timed_out,
                "killed": result.killed,
            }
        )
        _info(f"usage-log.jsonl appended (session_id={session_id})")
    except OSError as exc:
        _err(f"usage-log append failed: {exc}")

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        _info("interrupted by user.")
        sys.exit(2)
    except Exception as exc:  # noqa: BLE001
        _err(f"unexpected error: {exc}")
        sys.exit(99)
