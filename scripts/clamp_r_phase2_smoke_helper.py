#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""T-CLAMP-R-Train Phase 2 Smoke Actual Runner — Python helper.

Source: T-CLAMP-R-Train-Phase-2-Smoke-Execute-Spec/execute_spec.md (732 行 §0-§9)
Wrapper-only scope: no env / config / orchestrator touches. Reads stdout.log produced by
train_grip.py, writes RUN_METRICS.json v2 schema per Execute-Spec §6.1.

Sub-commands:
  preflight   GPU + demo + ground-truth + disk + orphan verification (Execute-Spec §2)
  monitor     stdout.log polling, T1/T2/T3 abort detection, SIGTERM dispatch (Execute-Spec §4)
  aggregate   merge summary.json + abort_summary.txt → RUN_METRICS.json v2 (Execute-Spec §6)
  verdict     read RUN_METRICS.json field for shell consumption
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

ITER_REGEX = re.compile(r"\biter[\s_=:-]*([0-9]+)\b", re.IGNORECASE)
SR_REGEX = re.compile(r"(?:best_metric|success_rate|sr)\s*[=:]\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)
VALUE_LOSS_REGEX = re.compile(r"value_?loss\s*[=:]\s*([0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)", re.IGNORECASE)
SURR_LOSS_REGEX = re.compile(r"surr(?:ogate)?_?loss\s*[=:]\s*([0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)", re.IGNORECASE)
ROLLBACK_REGEX = re.compile(r"surr_?rollback_?count\s*[=:]\s*([0-9]+)", re.IGNORECASE)
REWARD_REGEX = re.compile(r"reward(?:_mean)?\s*[=:]\s*(-?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)", re.IGNORECASE)
NAN_TOKEN = re.compile(r"\bnan\b", re.IGNORECASE)


def _print(tag: str, msg: str) -> None:
    print(f"[CLAMP-R-SMOKE-HELPER][{tag}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------

GROUND_TRUTH_VALUES = {
    # name: (expected, sanity description)
    "ALPHA_DIST_R_ONLY": (
        0.05,
        "penalty cumulated 600 step × -0.05 = -30 vs reward budget 7.0 = ratio 4.3:1 (<5:1 RED FLAG)",
    ),
    "R_TASK_BONUS_R_ONLY": (5.0, "task completion bonus, mirror of CLAMP-L"),
    "SEAT_THRESHOLD": (0.005, "5mm seat bonus distance, ground-truth reachability 6-10x margin"),
    "EPISODE_BUDGET": (600, "600 steps (5s @ dt=1/120), mirror of CLAMP-L"),
    "BC_REPLAY_ALPHA": (0.5, "50% demo replay + 50% PPO rollout per minibatch"),
}


def _check_gpu(device_idx: int, min_free_gb: float) -> bool:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.free,memory.total",
                "--format=csv,noheader,nounits",
                "-i",
                str(device_idx),
            ],
            text=True,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        _print("PREFLIGHT", f"GPU verify FAIL: {e}")
        return False
    free_mb_str, total_mb_str = (s.strip() for s in out.split(","))
    free_gb = float(free_mb_str) / 1024.0
    total_gb = float(total_mb_str) / 1024.0
    if free_gb < min_free_gb:
        _print(
            "PREFLIGHT", f"GPU#{device_idx} free {free_gb:.1f} GB < {min_free_gb} GB (total {total_gb:.1f} GB) — FAIL"
        )
        return False
    _print("PREFLIGHT", f"GPU#{device_idx} free {free_gb:.1f} GB / total {total_gb:.1f} GB — PASS")
    return True


def _check_demo(demo_path: Path) -> bool:
    if not demo_path.is_file():
        _print("PREFLIGHT", f"Demo file MISSING: {demo_path}")
        return False
    size_mb = demo_path.stat().st_size / (1024.0 * 1024.0)
    if size_mb < 1.0:
        _print("PREFLIGHT", f"Demo file too small ({size_mb:.2f} MB < 1 MB): {demo_path}")
        return False
    _print("PREFLIGHT", f"Demo file size {size_mb:.2f} MB — PASS ({demo_path})")
    return True


def _check_ground_truth() -> bool:
    _print(
        "PREFLIGHT", "Ground-truth values (printed for cross-check, no automatic env import to honor TOUCH FORBIDDEN):"
    )
    for name, (val, note) in GROUND_TRUTH_VALUES.items():
        _print("PREFLIGHT", f"  {name} = {val}  ({note})")
    return True


def _check_disk(log_base: Path, min_disk_gb: float) -> bool:
    log_base.mkdir(parents=True, exist_ok=True)
    free_bytes = shutil.disk_usage(log_base).free
    free_gb = free_bytes / (1024.0**3)
    if free_gb < min_disk_gb:
        _print("PREFLIGHT", f"Disk free {free_gb:.1f} GB < {min_disk_gb} GB — FAIL ({log_base})")
        return False
    _print("PREFLIGHT", f"Disk free {free_gb:.1f} GB — PASS ({log_base})")
    return True


def _check_orphan() -> bool:
    try:
        out = subprocess.check_output(["pgrep", "-fa", "train_grip.py"], text=True).strip()
    except subprocess.CalledProcessError:
        out = ""
    if out:
        _print("PREFLIGHT", f"Orphan train_grip.py process detected (FAIL):\n{out}")
        return False
    _print("PREFLIGHT", "No orphan train_grip.py process — PASS")
    return True


def cmd_preflight(args: argparse.Namespace) -> int:
    _print("PREFLIGHT", "Begin 5-cascade verify (Execute-Spec §2)")
    results = [
        ("GPU", _check_gpu(args.device_idx, args.min_free_gb)),
        ("Demo", _check_demo(Path(args.demo_path))),
        ("GroundTruth", _check_ground_truth()),
        ("Disk", _check_disk(Path(args.log_base), args.min_disk_gb)),
        ("Orphan", _check_orphan()),
    ]
    failed = [name for name, ok in results if not ok]
    if failed:
        _print("PREFLIGHT", f"FAILED checks: {', '.join(failed)}")
        return 1
    _print("PREFLIGHT", "All 5 checks PASS")
    return 0


# ---------------------------------------------------------------------------
# monitor
# ---------------------------------------------------------------------------


def _parse_iter_line(line: str) -> dict | None:
    if "iter" not in line.lower():
        return None
    iter_m = ITER_REGEX.search(line)
    if not iter_m:
        return None
    sr_m = SR_REGEX.search(line)
    if not sr_m:
        return None
    payload = {
        "iter": int(iter_m.group(1)),
        "sr": float(sr_m.group(1)),
    }
    vl_m = VALUE_LOSS_REGEX.search(line)
    if vl_m:
        payload["value_loss"] = float(vl_m.group(1))
    sl_m = SURR_LOSS_REGEX.search(line)
    if sl_m:
        payload["surr_loss"] = float(sl_m.group(1))
    rb_m = ROLLBACK_REGEX.search(line)
    if rb_m:
        payload["surr_rollback_count"] = int(rb_m.group(1))
    rw_m = REWARD_REGEX.search(line)
    if rw_m:
        payload["reward_mean"] = float(rw_m.group(1))
    payload["nan_in_line"] = bool(NAN_TOKEN.search(line))
    return payload


def _write_abort(log_dir: Path, tier: str, iter_idx: int, reason: str) -> None:
    abort_path = log_dir / "abort_summary.txt"
    payload = {
        "abort_tier": tier,
        "abort_iter": iter_idx,
        "abort_reason": reason,
        "abort_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }
    abort_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _print("MONITOR", f"abort_summary.txt written: tier={tier} iter={iter_idx}")


def _send_term(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
        _print("MONITOR", f"SIGTERM dispatched to PID={pid}")
    except ProcessLookupError:
        _print("MONITOR", f"PID={pid} already exited")
    except PermissionError as e:
        _print("MONITOR", f"SIGTERM denied to PID={pid}: {e}")


def cmd_monitor(args: argparse.Namespace) -> int:
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / "stdout.log"

    sr_window: deque[float] = deque(maxlen=max(args.t1_window, args.t2_window))
    aborted = False
    started = time.time()

    _print(
        "MONITOR",
        f"Begin polling stdout.log (T1 SR≥{args.t1_sr} for {args.t1_window} iters, "
        f"T2 SR<{args.t2_sr} for {args.t2_window} iters, wall_timeout={args.wall_timeout_sec}s)",
    )

    # Wait for stdout.log to appear (up to 60s)
    waited = 0
    while not stdout_path.exists() and waited < 60:
        time.sleep(1)
        waited += 1
    if not stdout_path.exists():
        _print("MONITOR", "stdout.log did not appear within 60s — exiting (no abort)")
        return 0

    with stdout_path.open("r", encoding="utf-8", errors="replace") as fh:
        # Skip to end (live tailing)
        fh.seek(0, os.SEEK_END)
        last_iter = -1
        while not aborted:
            now = time.time()
            wall = now - started
            if wall > args.wall_timeout_sec:
                _write_abort(log_dir, "T3g_WALL_TIMEOUT", last_iter, f"wall {wall:.0f}s > {args.wall_timeout_sec}s")
                if args.train_pid:
                    _send_term(args.train_pid)
                aborted = True
                break

            if args.train_pid:
                try:
                    os.kill(args.train_pid, 0)
                except ProcessLookupError:
                    _print("MONITOR", "train PID exited — stopping monitor")
                    return 0

            line = fh.readline()
            if not line:
                time.sleep(1)
                continue
            parsed = _parse_iter_line(line)
            if parsed is None:
                if NAN_TOKEN.search(line):
                    _write_abort(log_dir, "T3c_NAN", last_iter, f"NaN token detected in line: {line.strip()[:200]}")
                    if args.train_pid:
                        _send_term(args.train_pid)
                    aborted = True
                continue

            it = parsed["iter"]
            sr = parsed["sr"]
            last_iter = it
            sr_window.append(sr)

            # T3c: NaN in metrics
            for k in ("sr", "value_loss", "surr_loss", "reward_mean"):
                v = parsed.get(k)
                if v is not None and (math.isnan(v) or math.isinf(v)):
                    _write_abort(log_dir, "T3c_NAN", it, f"NaN/Inf in {k}={v}")
                    if args.train_pid:
                        _send_term(args.train_pid)
                    aborted = True
                    break
            if aborted:
                break

            # T3a: surr_rollback_count >= 3
            rb = parsed.get("surr_rollback_count")
            if rb is not None and rb >= 3:
                _write_abort(log_dir, "T3a_SURR_LOSS", it, f"surr_rollback_count={rb} >= 3")
                if args.train_pid:
                    _send_term(args.train_pid)
                aborted = True
                break

            # T3e: reward rolling mean < -100
            rw = parsed.get("reward_mean")
            if rw is not None and rw < -100.0:
                _write_abort(log_dir, "T3e_REWARD_COLLAPSE", it, f"reward_mean={rw} < -100")
                if args.train_pid:
                    _send_term(args.train_pid)
                aborted = True
                break

            # T1 saturation: last t1_window iters all SR >= t1_sr
            if len(sr_window) >= args.t1_window:
                last = list(sr_window)[-args.t1_window :]
                if all(s >= args.t1_sr for s in last):
                    _write_abort(
                        log_dir, "T1_SATURATION", it, f"SR>= {args.t1_sr} sustained {args.t1_window} iters: {last}"
                    )
                    if args.train_pid:
                        _send_term(args.train_pid)
                    aborted = True
                    break

            # T2 plateau: last t2_window iters all SR < t2_sr
            if len(sr_window) >= args.t2_window:
                last = list(sr_window)[-args.t2_window :]
                if all(s < args.t2_sr for s in last):
                    _write_abort(
                        log_dir, "T2_PLATEAU", it, f"SR< {args.t2_sr} sustained {args.t2_window} iters: {last}"
                    )
                    if args.train_pid:
                        _send_term(args.train_pid)
                    aborted = True
                    break

            # Stop after max_iter (defensive; train_grip.py should self-stop)
            if it >= args.max_iter:
                _print("MONITOR", f"max_iter reached (iter={it}); stop monitoring")
                break

    _print("MONITOR", f"Monitor exit (aborted={aborted})")
    return 0


# ---------------------------------------------------------------------------
# aggregate
# ---------------------------------------------------------------------------


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(Path(__file__).resolve().parent.parent), text=True
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def _scan_stdout_per_iter(stdout_path: Path, iter_max: int) -> dict[str, list[float | None]]:
    best = [None] * iter_max
    vloss = [None] * iter_max
    rew = [None] * iter_max
    surr_rb_max = 0
    if not stdout_path.is_file():
        return {
            "best_metric_per_iter": [float("nan") if x is None else x for x in best],
            "value_loss_max_per_iter": [float("nan") if x is None else x for x in vloss],
            "reward_mean_per_iter": [float("nan") if x is None else x for x in rew],
            "surr_rollback_count": surr_rb_max,
        }
    with stdout_path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parsed = _parse_iter_line(line)
            if parsed is None:
                continue
            i = parsed["iter"]
            if not (1 <= i <= iter_max):
                continue
            idx = i - 1
            if "sr" in parsed:
                if best[idx] is None or parsed["sr"] > best[idx]:
                    best[idx] = parsed["sr"]
            if "value_loss" in parsed:
                if vloss[idx] is None or parsed["value_loss"] > vloss[idx]:
                    vloss[idx] = parsed["value_loss"]
            if "reward_mean" in parsed:
                if rew[idx] is None:
                    rew[idx] = parsed["reward_mean"]
            rb = parsed.get("surr_rollback_count")
            if rb is not None and rb > surr_rb_max:
                surr_rb_max = rb
    return {
        "best_metric_per_iter": [float("nan") if x is None else x for x in best],
        "value_loss_max_per_iter": [float("nan") if x is None else x for x in vloss],
        "reward_mean_per_iter": [float("nan") if x is None else x for x in rew],
        "surr_rollback_count": surr_rb_max,
    }


def _resolve_verdict(abort_tier: str) -> str:
    if abort_tier == "T1_SATURATION":
        return "SUCCESS_PROMOTE_MULTI_SEED"
    if abort_tier == "T2_PLATEAU":
        return "FAIL_NO_SIGNAL_REDESIGN"
    if abort_tier.startswith("T3"):
        return "FAIL_CATASTROPHE_FRESH_RESTART"
    if abort_tier == "RESULT_INCONCLUSIVE":
        return "RESULT_INCONCLUSIVE_RERUN_OR_ESCALATE"
    if abort_tier == "COMPLETED":
        return "RESULT_INCONCLUSIVE_RERUN_OR_ESCALATE"
    return "RESULT_INCONCLUSIVE_RERUN_OR_ESCALATE"


def _next_action_for(verdict: str) -> str:
    if verdict == "SUCCESS_PROMOTE_MULTI_SEED":
        return (
            "Spawn T-CLAMP-R-Train-Phase-3-Multi-Seed-Promote (5 seed × 1000 iter × cuda:2) per "
            "Smoke-Plan §3.1 next_action; run post-train det eval first to confirm SR>=30%."
        )
    if verdict == "FAIL_NO_SIGNAL_REDESIGN":
        return (
            "Per Phase-3-Future-Roadmap-Draft, choose among: A1 Reward Redesign, A2 Demo Redesign, "
            "A3 Architecture Rethink, or A4 NHA HOLD ★ NULL acceptance (Path Y precedent #9)."
        )
    if verdict == "FAIL_CATASTROPHE_FRESH_RESTART":
        return (
            "Forensic checkpoint marked, resume forbidden (prohibited.md L40). Choose: B1 Reward Tighten "
            "(α=0.025), B2 Demo Expand (100 demos), B3 Initial State Narrow, or B4 NHA HOLD ★."
        )
    return (
        "Inconclusive: 50 iter complete with no T1/T2/T3 signal. Options: 100-iter extension, full "
        "training escalate, or NHA HOLD ★ NULL acceptance."
    )


def _read_abort_summary(log_dir: Path) -> tuple[str, int, str | None]:
    path = log_dir / "abort_summary.txt"
    if not path.is_file():
        return ("COMPLETED", 0, None)
    raw = path.read_text(encoding="utf-8").strip()
    try:
        payload = json.loads(raw)
        return (
            str(payload.get("abort_tier", "COMPLETED")),
            int(payload.get("abort_iter", 0)),
            payload.get("abort_reason"),
        )
    except json.JSONDecodeError:
        return ("COMPLETED", 0, None)


def cmd_aggregate(args: argparse.Namespace) -> int:
    log_dir = Path(args.log_dir)
    metrics_dir = Path(args.metrics_dir)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    abort_tier, abort_iter, abort_reason = _read_abort_summary(log_dir)
    iter_data = _scan_stdout_per_iter(log_dir / "stdout.log", args.iter_max)

    iter_actual = sum(1 for x in iter_data["best_metric_per_iter"] if not (isinstance(x, float) and math.isnan(x)))
    if abort_tier == "COMPLETED" and iter_actual < args.iter_max:
        abort_tier = "RESULT_INCONCLUSIVE"

    started_at = (
        (log_dir / "started_at.txt").read_text(encoding="utf-8").strip()
        if (log_dir / "started_at.txt").is_file()
        else None
    )
    completed_at = (
        (log_dir / "completed_at.txt").read_text(encoding="utf-8").strip()
        if (log_dir / "completed_at.txt").is_file()
        else _dt.datetime.now(_dt.timezone.utc).isoformat()
    )
    wall = None
    if started_at and completed_at:
        try:
            wall = (_dt.datetime.fromisoformat(completed_at) - _dt.datetime.fromisoformat(started_at)).total_seconds()
        except ValueError:
            wall = None

    train_summary_path = log_dir / "summary.json"
    if not train_summary_path.is_file():
        train_summary_path = log_dir / "train_summary.json"
    train_summary = None
    if train_summary_path.is_file():
        try:
            train_summary = json.loads(train_summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            train_summary = None

    best_final = max(
        (x for x in iter_data["best_metric_per_iter"] if isinstance(x, (int, float)) and not math.isnan(x)),
        default=float("nan"),
    )

    forensic_path = None
    if abort_tier.startswith("T3"):
        candidate = log_dir / f"forensic_iter_{abort_iter}.pt"
        # We do not move model_best.pt here (TOUCH FORBIDDEN — we only mark by path string).
        # The forensic.pt suffix convention is enforced by Execute-Spec §3.4; actual rename
        # is responsibility of the train_grip.py side or a follow-up forensic step.
        forensic_path = str(candidate)

    verdict = _resolve_verdict(abort_tier)
    next_action = _next_action_for(verdict)

    payload = {
        "schema_version": "v2",
        "run_id": args.run_id,
        "skill": "clamp_r",
        "phase": "smoke",
        "seed": args.seed,
        "expected_arm": args.expected_arm,
        "selected_success_semantics_version": (
            train_summary.get("selected_success_semantics_version") if train_summary else "b5_expected_arm_v1"
        ),
        "train_summary_expected_arm": train_summary.get("expected_arm") if train_summary else None,
        "iter_max": args.iter_max,
        "iter_actual": iter_actual,
        "abort_tier": abort_tier,
        "abort_iter": abort_iter,
        "abort_reason": abort_reason,
        "wall_clock_sec": wall,
        "gpu_max_mem_used_mb": None,
        "best_metric_per_iter": iter_data["best_metric_per_iter"],
        "best_metric_final": best_final if not (isinstance(best_final, float) and math.isnan(best_final)) else None,
        "value_loss_max_per_iter": iter_data["value_loss_max_per_iter"],
        "reward_mean_per_iter": iter_data["reward_mean_per_iter"],
        "surr_rollback_count": iter_data["surr_rollback_count"],
        "det_eval_post_path": "T1_PASS_executed"
        if verdict == "SUCCESS_PROMOTE_MULTI_SEED"
        else (
            "NOT_executed_T2_T3_abort"
            if verdict in ("FAIL_NO_SIGNAL_REDESIGN", "FAIL_CATASTROPHE_FRESH_RESTART")
            else "NOT_executed_RESULT_INCONCLUSIVE"
        ),
        "det_eval_SR": None,
        "det_eval_per_clip_SR": None,
        "forensic_checkpoint_path": forensic_path,
        "env_config_snapshot_sha256": _sha256(log_dir / "env_config_snapshot.json"),
        "demo_dataset_sha256": _sha256(Path(args.demo_path)),
        "train_summary_present": train_summary is not None,
        "train_exit_code": args.train_exit_code,
        "git_head": _git_head(),
        "started_at": started_at,
        "completed_at": completed_at,
        "verdict": verdict,
        "next_action_recommendation": next_action,
        "rs_disposition_pending": True,
    }

    out = metrics_dir / "RUN_METRICS.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    os.replace(tmp, out)
    _print("AGGREGATE", f"Written {out}")
    return 0


# ---------------------------------------------------------------------------
# verdict
# ---------------------------------------------------------------------------


def cmd_verdict(args: argparse.Namespace) -> int:
    path = Path(args.metrics_json)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if args.field not in payload:
        print("UNKNOWN")
        return 1
    val = payload[args.field]
    if isinstance(val, (dict, list)):
        print(json.dumps(val))
    else:
        print(val)
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pre = sub.add_parser("preflight")
    p_pre.add_argument("--device-idx", type=int, default=2)
    p_pre.add_argument("--demo-path", required=True)
    p_pre.add_argument("--log-base", required=True)
    p_pre.add_argument("--min-free-gb", type=float, default=23.0)
    p_pre.add_argument("--min-disk-gb", type=float, default=5.0)
    p_pre.set_defaults(func=cmd_preflight)

    p_mon = sub.add_parser("monitor")
    p_mon.add_argument("--log-dir", required=True)
    p_mon.add_argument("--max-iter", type=int, default=50)
    p_mon.add_argument("--train-pid", type=int, default=0)
    p_mon.add_argument("--t1-sr", type=float, default=0.30)
    p_mon.add_argument("--t1-window", type=int, default=5)
    p_mon.add_argument("--t2-sr", type=float, default=0.05)
    p_mon.add_argument("--t2-window", type=int, default=10)
    p_mon.add_argument("--wall-timeout-sec", type=int, default=130 * 60)
    p_mon.set_defaults(func=cmd_monitor)

    p_agg = sub.add_parser("aggregate")
    p_agg.add_argument("--log-dir", required=True)
    p_agg.add_argument("--metrics-dir", required=True)
    p_agg.add_argument("--run-id", required=True)
    p_agg.add_argument("--seed", type=int, required=True)
    p_agg.add_argument("--expected-arm", default="right", choices=["right", "left", "both"])
    p_agg.add_argument("--iter-max", type=int, default=50)
    p_agg.add_argument("--demo-path", required=True)
    p_agg.add_argument("--train-exit-code", type=int, default=0)
    p_agg.set_defaults(func=cmd_aggregate)

    p_ver = sub.add_parser("verdict")
    p_ver.add_argument("--metrics-json", required=True)
    p_ver.add_argument("--field", default="verdict")
    p_ver.set_defaults(func=cmd_verdict)

    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
