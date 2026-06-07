#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""RobotTAS v1 IK Validate Wrapper.

Provides a stable API for invoking ``dry_run_43step.py`` as a subprocess,
with path whitelisting, atomic JSON writes, timestamp-suffixed backups,
usage logging, and edit field validation.

This wrapper is consumed by both ``robottas_mini.py`` (Phase 1b CLI frontend)
and a future ``robottas_v1.py`` (Phase 2 conditional GUI frontend). The
wrapper API is stable; frontends may be swapped without re-implementing
subprocess handling, safety checks, or log I/O.

See ``thread-vault/09-RobotTAS-v1/api-contract.md`` for the full contract.
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Literal, TypedDict

# -- Module-level constants ---------------------------------------------------

_THIS = Path(__file__).resolve()
REPO_ROOT = _THIS.parents[2]  # scripts/ -> thread_isaac_lab/ -> IsaacLab/
DRY_RUN_SCRIPT = REPO_ROOT / "thread_isaac_lab" / "scripts" / "dry_run_43step.py"
VALID_JSON_DIR = REPO_ROOT / "thread_isaac_lab" / "data" / "waypoints"
CONFIG_DIR = REPO_ROOT / "thread_isaac_lab" / "configs"
BACKUP_DIR = REPO_ROOT / "thread_isaac_lab" / "thread-vault" / "09-RobotTAS-v1" / "backups"
USAGE_LOG = REPO_ROOT / "thread_isaac_lab" / "thread-vault" / "09-RobotTAS-v1" / "usage-log.jsonl"

DEFAULT_TIMEOUT_S = 60
ALLOWED_DEVICES = frozenset({"cuda:0", "cuda:1", "cuda:2"})
ALLOWED_EDIT_FIELDS = frozenset(
    {
        "target_l.x",
        "target_l.y",
        "target_l.z",
        "target_r.x",
        "target_r.y",
        "target_r.z",
        "left_finger",
        "right_finger",
    }
)
BACKUP_RE = re.compile(r"^full_43step\.json\.pre_robottas_v1_backup_(\d{14})\.json$")
JST = datetime.timezone(datetime.timedelta(hours=9))

# -- Result types -------------------------------------------------------------


class StepResult(TypedDict):
    """Per-step result read back from full_43step.json after dry-run."""

    step: int
    phase: str
    desc: str
    target_l: list[float]
    target_r: list[float]
    left_finger: float
    right_finger: float
    err_l_mm: float
    err_r_mm: float
    status: Literal["PASS", "FAIL"]


class Summary(TypedDict):
    """Aggregate summary from dry_run_43step.py."""

    total: int
    # JSON key is "pass"; Python reserved word dodged at read time.
    pass_: int
    fail: int


@dataclasses.dataclass
class InvokeResult:
    """Structured result of ``invoke_dry_run``."""

    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    updated_steps: list[StepResult] | None
    updated_summary: Summary | None
    timed_out: bool
    killed: bool


# -- Public API ---------------------------------------------------------------


def validate_edit_field(field: str) -> tuple[str, int]:
    """Parse and validate a UI-owned edit field specifier.

    Args:
        field: One of ``target_l.x|.y|.z``, ``target_r.x|.y|.z``,
            ``left_finger``, ``right_finger``.

    Returns:
        Tuple ``(field_name, index)``. For vector fields the index is
        ``0/1/2`` for ``x/y/z``; for scalar fields the index is ``-1``.

    Raises:
        ValueError: ``field`` is not in the whitelist (Frozen field guard).
    """
    if field not in ALLOWED_EDIT_FIELDS:
        raise ValueError(f"Field {field!r} is not in UI-owned whitelist. Allowed: {sorted(ALLOWED_EDIT_FIELDS)}")
    if "." in field:
        name, comp = field.split(".", 1)
        return name, {"x": 0, "y": 1, "z": 2}[comp]
    return field, -1


def _check_path_whitelist(waypoint_json: Path) -> Path:
    """Resolve ``waypoint_json`` and assert it lives inside ``VALID_JSON_DIR``."""
    resolved = waypoint_json.resolve()
    base = VALID_JSON_DIR.resolve()
    try:
        resolved.relative_to(base)
    except ValueError:
        raise ValueError(
            f"waypoint_json {waypoint_json} resolves to {resolved}, which is outside VALID_JSON_DIR {base}."
        )
    return resolved


def atomic_write_json(path: Path, data: dict) -> None:
    """Write ``data`` to ``path`` atomically (tempfile + fsync + rename)."""
    path = Path(path)
    target_dir = path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=target_dir, prefix=".robottas_tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp_path, path)
    except Exception:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_path)
        raise


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def list_backups() -> list[Path]:
    """Return sorted backup file paths (oldest first, strict-format only)."""
    if not BACKUP_DIR.exists():
        return []
    entries: list[tuple[str, Path]] = []
    for p in BACKUP_DIR.iterdir():
        if not p.is_file():
            continue
        m = BACKUP_RE.match(p.name)
        if m:
            entries.append((m.group(1), p))
    entries.sort()  # Lexical on 14-digit timestamp is chronological.
    return [p for _, p in entries]


def create_backup(waypoint_json: Path, *, skip_if_exists: bool = True) -> Path | None:
    """Create a timestamp-suffixed backup under ``BACKUP_DIR``.

    Args:
        waypoint_json: Source file to back up; must be inside ``VALID_JSON_DIR``.
        skip_if_exists: If ``True`` (default) and any RobotTAS v1 backup already
            exists, return ``None`` so the oldest baseline is preserved.

    Returns:
        Path of the new backup, or ``None`` if skipped.
    """
    waypoint_json = _check_path_whitelist(waypoint_json)
    if not waypoint_json.is_file():
        raise FileNotFoundError(f"waypoint_json not found: {waypoint_json}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    existing = list_backups()
    if skip_if_exists and existing:
        return None
    ts = datetime.datetime.now(JST).strftime("%Y%m%d%H%M%S")
    dest = BACKUP_DIR / f"full_43step.json.pre_robottas_v1_backup_{ts}.json"
    # Use atomic write for the backup copy so partial writes can't produce a
    # truncated "baseline" on SIGKILL.
    with open(waypoint_json, "rb") as src:
        data = src.read()
    fd, tmp_path = tempfile.mkstemp(dir=BACKUP_DIR, prefix=".robottas_tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp_path, dest)
    except Exception:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_path)
        raise
    return dest


def restore_backup(
    backup_path: Path,
    waypoint_json: Path,
    *,
    verify_hash: str | None = None,
) -> bool:
    """Restore ``waypoint_json`` from ``backup_path`` via atomic copy.

    Args:
        backup_path: Backup file, must live under ``BACKUP_DIR``.
        waypoint_json: Target file; must be inside ``VALID_JSON_DIR``.
        verify_hash: If given, assert that ``sha256(backup_path) == verify_hash``
            before copying (dirty-edit detection).

    Returns:
        ``True`` on successful restore.

    Raises:
        ValueError: Path whitelist violation or hash mismatch.
    """
    backup_path = Path(backup_path).resolve()
    try:
        backup_path.relative_to(BACKUP_DIR.resolve())
    except ValueError:
        raise ValueError(f"backup_path {backup_path} is outside BACKUP_DIR")
    if not backup_path.is_file():
        raise FileNotFoundError(f"backup_path not found: {backup_path}")
    if verify_hash is not None:
        got = _sha256(backup_path)
        if got != verify_hash:
            raise ValueError(
                f"backup hash mismatch: expected {verify_hash}, got {got}. "
                f"Dirty-edit detected; escalate to rs (BLOCKED_FOR_USER)."
            )
    waypoint_json = _check_path_whitelist(waypoint_json)
    with open(backup_path) as f:
        data = json.load(f)
    atomic_write_json(waypoint_json, data)
    return True


def append_usage_log(record: dict) -> None:
    """Append a single JSON record to ``USAGE_LOG`` under exclusive file lock."""
    USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with open(USAGE_LOG, "a", encoding="utf-8") as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def _parse_summary(raw: dict | None) -> Summary | None:
    if raw is None:
        return None
    return {
        "total": int(raw.get("total", 0)),
        "pass_": int(raw.get("pass", 0)),
        "fail": int(raw.get("fail", 0)),
    }


def invoke_dry_run(
    waypoint_json: Path,
    device: str,
    *,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    python_exe: Path | None = None,
) -> InvokeResult:
    """Invoke ``dry_run_43step.py`` as a subprocess and capture the result.

    Args:
        waypoint_json: Path to the JSON to validate, must live in
            ``VALID_JSON_DIR``.
        device: One of ``cuda:0``, ``cuda:1``, ``cuda:2``.
        timeout_s: Hard wall-clock timeout for the subprocess.
        python_exe: Python interpreter path; defaults to ``sys.executable``.

    Returns:
        ``InvokeResult`` with returncode, stdout, stderr, duration, updated
        ``steps`` + ``summary`` read back from the JSON, and timeout/killed
        flags.
    """
    waypoint_json = _check_path_whitelist(waypoint_json)
    if not waypoint_json.is_file():
        raise FileNotFoundError(f"waypoint_json not found: {waypoint_json}")
    if device not in ALLOWED_DEVICES:
        raise ValueError(f"device {device!r} not allowed. Allowed: {sorted(ALLOWED_DEVICES)}")
    py = Path(python_exe) if python_exe is not None else Path(sys.executable)

    env = {
        **os.environ,
        "THREAD_CONFIG_DIR": str(CONFIG_DIR.resolve()),
        "NEWTON_DEVICE": device,
    }

    start = time.monotonic()
    timed_out = False
    killed = False
    try:
        proc = subprocess.Popen(
            [str(py), str(DRY_RUN_SCRIPT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            cwd=str(REPO_ROOT),
            env=env,
            shell=False,
            start_new_session=True,  # orphan prevention
            text=True,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Failed to spawn subprocess: {exc}") from exc

    try:
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
            stdout, stderr = proc.communicate()
            rc = proc.returncode if proc.returncode is not None else -1
    except KeyboardInterrupt:
        killed = True
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        stdout, stderr = proc.communicate()
        rc = proc.returncode if proc.returncode is not None else -1
        duration = time.monotonic() - start
        return InvokeResult(
            returncode=rc,
            stdout=stdout or "",
            stderr=stderr or "",
            duration_seconds=duration,
            updated_steps=None,
            updated_summary=None,
            timed_out=False,
            killed=True,
        )
    duration = time.monotonic() - start

    updated_steps: list[StepResult] | None = None
    updated_summary: Summary | None = None
    if not timed_out and not killed:
        try:
            with open(waypoint_json) as f:
                data = json.load(f)
            updated_steps = data.get("steps")
            updated_summary = _parse_summary(data.get("summary"))
        except (OSError, json.JSONDecodeError):
            # Subprocess may have been killed mid-write; read-back not
            # guaranteed. Leave updated_* as None.
            pass

    return InvokeResult(
        returncode=rc,
        stdout=stdout or "",
        stderr=stderr or "",
        duration_seconds=duration,
        updated_steps=updated_steps,
        updated_summary=updated_summary,
        timed_out=timed_out,
        killed=False,
    )


def now_jst_iso() -> str:
    """Return current JST time as an ISO 8601 string (for usage-log timestamps)."""
    return datetime.datetime.now(JST).isoformat(timespec="seconds")
