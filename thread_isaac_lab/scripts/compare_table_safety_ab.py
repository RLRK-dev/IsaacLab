#!/usr/bin/env python3
"""Summarize table safety A/B runs into a single TSV.

This script intentionally distinguishes "unavailable" contact signals from zeros.
Missing/null values are emitted as "NA" instead of 0.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from typing import Any


def _iter_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def _load_json(path: str) -> dict[str, Any] | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _event_field(evt: dict[str, Any], key: str) -> Any:
    if key in evt:
        return evt.get(key)
    payload = evt.get("payload")
    if isinstance(payload, dict):
        return payload.get(key)
    return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "on", "y"}:
        return True
    if s in {"0", "false", "no", "off", "n"}:
        return False
    return None


def _safe_max(values: list[int | float]) -> int | float | None:
    return max(values) if values else None


def _safe_min(values: list[int | float]) -> int | float | None:
    return min(values) if values else None


def _file_nonempty(path: str) -> bool:
    return os.path.exists(path) and os.path.getsize(path) > 0


def _log_path(out_dir: str) -> str | None:
    for name in ("ab_run.log", "poc_stdout.log"):
        p = os.path.join(out_dir, name)
        if os.path.exists(p):
            return p
    return None


def _extract_contract_init_stagnation(log_path: str | None) -> int | None:
    if not log_path or not os.path.exists(log_path):
        return None
    patt = re.compile(r"\[PoC\]\[CONTRACT\].*stagnation_steps=(\d+)/\d+")
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = patt.search(line)
            if m:
                try:
                    return int(m.group(1))
                except (TypeError, ValueError):
                    return None
    return None


def _extract_last_result_line(log_path: str | None) -> str | None:
    if not log_path or not os.path.exists(log_path):
        return None
    last: str | None = None
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "[PoC] Result:" in line:
                last = line.strip()
    return last


def _count_stdout_table_safety(log_path: str | None) -> int:
    if not log_path or not os.path.exists(log_path):
        return 0
    cnt = 0
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "[PoC][TABLE_SAFETY]" in line:
                cnt += 1
    return cnt


def _infer_run_id(out_dir: str) -> str:
    summary_path = os.path.join(out_dir, "RUN_SUMMARY.json")
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            run_id = obj.get("run_id")
            if isinstance(run_id, str) and run_id.strip():
                return run_id.strip()
        except Exception:
            pass
    base = os.path.basename(os.path.normpath(out_dir))
    if base.startswith("test_"):
        return base[len("test_") :]
    return base


def summarize_out_dir(out_dir: str, contacts_valid_ratio_threshold: float) -> dict[str, Any]:
    eps = 1e-6
    run_metrics_path = os.path.join(out_dir, "RUN_METRICS.json")
    contacts_rows = _iter_jsonl(os.path.join(out_dir, "sensors", "contacts.jsonl"))
    state_rows = _iter_jsonl(os.path.join(out_dir, "sensors", "state.jsonl"))
    events_rows = _iter_jsonl(os.path.join(out_dir, "sensors", "events.jsonl"))
    log_path = _log_path(out_dir)
    run_metrics = _load_json(run_metrics_path)

    run_metrics_present = os.path.exists(run_metrics_path)
    run_metrics_parse_ok = run_metrics is not None
    run_metrics_final = _as_bool((run_metrics or {}).get("final"))
    run_metrics_exit_code = _as_int(((run_metrics or {}).get("run") or {}).get("exit_code"))

    artifact_poc_stdout_ok = _file_nonempty(os.path.join(out_dir, "poc_stdout.log"))
    artifact_state_ok = _file_nonempty(os.path.join(out_dir, "sensors", "state.jsonl"))
    artifact_events_ok = _file_nonempty(os.path.join(out_dir, "sensors", "events.jsonl"))
    artifact_contacts_ok = _file_nonempty(os.path.join(out_dir, "sensors", "contacts.jsonl"))

    run_healthy_minimal = (
        run_metrics_parse_ok
        and (run_metrics_final is True)
        and (run_metrics_exit_code == 0)
        and artifact_poc_stdout_ok
        and artifact_state_ok
        and artifact_events_ok
        and artifact_contacts_ok
    )

    collision_streak_vals = [
        v
        for v in (_as_int(r.get("collision_any_streak_steps")) for r in contacts_rows)
        if v is not None
    ]
    max_collision_any_streak = _safe_max(collision_streak_vals)

    left_table_contacts_vals = [
        v
        for v in (_as_int(r.get("left_table_contacts_ge_threshold")) for r in contacts_rows)
        if v is not None
    ]
    max_left_table_contacts = _safe_max(left_table_contacts_vals)

    left_table_force_vals = [
        v
        for v in (_as_float(r.get("left_table_max_force_n")) for r in contacts_rows)
        if v is not None
    ]
    max_left_table_force = _safe_max(left_table_force_vals)

    contacts_available_vals = [
        v
        for v in (_as_bool(r.get("contacts_available")) for r in contacts_rows)
        if v is not None
    ]
    contacts_available_any = (any(contacts_available_vals) if contacts_available_vals else None)
    contacts_available_ratio = (
        (sum(1 for v in contacts_available_vals if v) / float(len(contacts_available_vals)))
        if contacts_available_vals
        else None
    )

    contacts_non_null_ratio_vals = [
        v
        for v in (_as_float(r.get("contacts_non_null_ratio")) for r in contacts_rows)
        if v is not None
    ]
    contacts_non_null_ratio_min = _safe_min(contacts_non_null_ratio_vals)
    contacts_non_null_ratio_max = _safe_max(contacts_non_null_ratio_vals)
    if contacts_non_null_ratio_min is None:
        contacts_sensor_status = "UNAVAILABLE"
    elif contacts_non_null_ratio_min + eps < float(contacts_valid_ratio_threshold):
        contacts_sensor_status = "DEGRADED"
    else:
        contacts_sensor_status = "OK"
    collision_metrics_valid = contacts_sensor_status == "OK"
    collision_eval_status = "OK" if collision_metrics_valid else "PASS_PENDING_SENSOR"

    ee_z_vals: list[float] = []
    for row in state_rows:
        ee = row.get("ee_pos_w")
        if isinstance(ee, list) and len(ee) >= 3:
            z = _as_float(ee[2])
            if z is not None:
                ee_z_vals.append(z)
    min_ee_z = _safe_min(ee_z_vals)

    table_events = [r for r in events_rows if str(r.get("event", "")) == "TABLE_SAFETY_ADJUST"]
    table_safety_event_count = len(table_events)
    table_contact_gate_count = sum(1 for r in table_events if _as_bool(_event_field(r, "table_contact_gate")) is True)
    table_escape_applied_count = sum(1 for r in table_events if _as_bool(_event_field(r, "table_escape_applied")) is True)
    no_contacts_fallback_gate_count = sum(
        1 for r in table_events if _as_bool(_event_field(r, "no_contacts_fallback_gate")) is True
    )
    z_floor_only_count = sum(
        1
        for r in table_events
        if (_as_bool(_event_field(r, "z_floor_clamped")) is True)
        and (_as_bool(_event_field(r, "table_escape_applied")) is not True)
    )
    desired_z_after_ge_floor_count = 0
    desired_z_after_lt_floor_count = 0
    desired_z_after_ge_target_count = 0
    desired_z_after_lt_target_count = 0
    for r in table_events:
        desired_after = _as_float(_event_field(r, "desired_z_after_m"))
        floor_z = _as_float(_event_field(r, "table_min_ee_z_m"))
        target_z = _as_float(_event_field(r, "z_target_min_m"))
        if desired_after is None or floor_z is None:
            continue
        if desired_after >= (floor_z - eps):
            desired_z_after_ge_floor_count += 1
        else:
            desired_z_after_lt_floor_count += 1
        if target_z is None:
            target_z = floor_z
        if desired_after >= (target_z - eps):
            desired_z_after_ge_target_count += 1
        else:
            desired_z_after_lt_target_count += 1

    collision_start_count = sum(1 for r in events_rows if str(r.get("event", "")) == "collision_start")
    collision_end_count = sum(1 for r in events_rows if str(r.get("event", "")) == "collision_end")
    vision_stuck_confirmed_count = sum(1 for r in events_rows if str(r.get("event", "")) == "VISION_STUCK_CONFIRMED")
    vision_stuck_recovery_applied_count = sum(
        1 for r in events_rows if str(r.get("event", "")) == "VISION_STUCK_RECOVERY_APPLIED"
    )
    vision_stuck_recovered_count = sum(1 for r in events_rows if str(r.get("event", "")) == "VISION_STUCK_RECOVERED")
    vision_stuck_recovery_failed_count = sum(
        1 for r in events_rows if str(r.get("event", "")) == "VISION_STUCK_RECOVERY_FAILED"
    )
    vision_track_unavailable_count = sum(
        1 for r in events_rows if str(r.get("event", "")) == "VISION_TRACK_UNAVAILABLE"
    )
    collision_start_count_effective = collision_start_count if collision_metrics_valid else None
    collision_end_count_effective = collision_end_count if collision_metrics_valid else None
    max_collision_any_streak_effective = max_collision_any_streak if collision_metrics_valid else None
    max_left_table_contacts_effective = max_left_table_contacts if collision_metrics_valid else None
    max_left_table_force_effective = max_left_table_force if collision_metrics_valid else None

    return {
        "run_id": _infer_run_id(out_dir),
        "contract_init_stagnation_steps": _extract_contract_init_stagnation(log_path),
        "run_metrics_present": run_metrics_present,
        "run_metrics_parse_ok": run_metrics_parse_ok,
        "run_metrics_final": run_metrics_final,
        "run_metrics_exit_code": run_metrics_exit_code,
        "artifact_poc_stdout_ok": artifact_poc_stdout_ok,
        "artifact_state_ok": artifact_state_ok,
        "artifact_events_ok": artifact_events_ok,
        "artifact_contacts_ok": artifact_contacts_ok,
        "run_healthy_minimal": run_healthy_minimal,
        "contacts_valid_ratio_threshold": contacts_valid_ratio_threshold,
        "contacts_sensor_status": contacts_sensor_status,
        "collision_metrics_valid": collision_metrics_valid,
        "collision_eval_status": collision_eval_status,
        "contacts_available_any": contacts_available_any,
        "contacts_available_ratio": contacts_available_ratio,
        "contacts_non_null_ratio_min": contacts_non_null_ratio_min,
        "contacts_non_null_ratio_max": contacts_non_null_ratio_max,
        "max_collision_any_streak": max_collision_any_streak,
        "max_collision_any_streak_effective": max_collision_any_streak_effective,
        "max_left_table_contacts_ge_threshold": max_left_table_contacts,
        "max_left_table_contacts_ge_threshold_effective": max_left_table_contacts_effective,
        "max_left_table_force_n": max_left_table_force,
        "max_left_table_force_n_effective": max_left_table_force_effective,
        "min_ee_z": min_ee_z,
        "TABLE_SAFETY_stdout_count": _count_stdout_table_safety(log_path),
        "TABLE_SAFETY_event_count": table_safety_event_count,
        "table_contact_gate_count": table_contact_gate_count,
        "table_escape_applied_count": table_escape_applied_count,
        "no_contacts_fallback_gate_count": no_contacts_fallback_gate_count,
        "z_floor_only_count": z_floor_only_count,
        "desired_z_after_ge_floor_count": desired_z_after_ge_floor_count,
        "desired_z_after_lt_floor_count": desired_z_after_lt_floor_count,
        "desired_z_after_ge_target_count": desired_z_after_ge_target_count,
        "desired_z_after_lt_target_count": desired_z_after_lt_target_count,
        "collision_start_count": collision_start_count,
        "collision_start_count_effective": collision_start_count_effective,
        "collision_end_count": collision_end_count,
        "collision_end_count_effective": collision_end_count_effective,
        "vision_stuck_confirmed_count": vision_stuck_confirmed_count,
        "vision_stuck_recovery_applied_count": vision_stuck_recovery_applied_count,
        "vision_stuck_recovered_count": vision_stuck_recovered_count,
        "vision_stuck_recovery_failed_count": vision_stuck_recovery_failed_count,
        "vision_track_unavailable_count": vision_track_unavailable_count,
        "last_result_line": _extract_last_result_line(log_path),
        "out_dir": out_dir,
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.10g}"
    text = str(value)
    return text.replace("\t", " ").replace("\n", " ").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize table-safety A/B runs into TSV.")
    parser.add_argument(
        "--out-dir",
        action="append",
        required=True,
        help="Run output directory (e.g. /.../data/test_<run_id>). Repeat for A/B runs.",
    )
    parser.add_argument("--output", required=True, help="Output TSV path.")
    parser.add_argument(
        "--contacts-valid-ratio-threshold",
        type=float,
        default=0.99,
        help="Minimum contacts_non_null_ratio_min for collision metrics to be treated as valid.",
    )
    args = parser.parse_args()

    columns = [
        "run_id",
        "contract_init_stagnation_steps",
        "run_metrics_present",
        "run_metrics_parse_ok",
        "run_metrics_final",
        "run_metrics_exit_code",
        "artifact_poc_stdout_ok",
        "artifact_state_ok",
        "artifact_events_ok",
        "artifact_contacts_ok",
        "run_healthy_minimal",
        "contacts_valid_ratio_threshold",
        "contacts_sensor_status",
        "collision_metrics_valid",
        "collision_eval_status",
        "contacts_available_any",
        "contacts_available_ratio",
        "contacts_non_null_ratio_min",
        "contacts_non_null_ratio_max",
        "max_collision_any_streak",
        "max_collision_any_streak_effective",
        "max_left_table_contacts_ge_threshold",
        "max_left_table_contacts_ge_threshold_effective",
        "max_left_table_force_n",
        "max_left_table_force_n_effective",
        "min_ee_z",
        "TABLE_SAFETY_stdout_count",
        "TABLE_SAFETY_event_count",
        "table_contact_gate_count",
        "table_escape_applied_count",
        "no_contacts_fallback_gate_count",
        "z_floor_only_count",
        "desired_z_after_ge_floor_count",
        "desired_z_after_lt_floor_count",
        "desired_z_after_ge_target_count",
        "desired_z_after_lt_target_count",
        "collision_start_count",
        "collision_start_count_effective",
        "collision_end_count",
        "collision_end_count_effective",
        "vision_stuck_confirmed_count",
        "vision_stuck_recovery_applied_count",
        "vision_stuck_recovered_count",
        "vision_stuck_recovery_failed_count",
        "vision_track_unavailable_count",
        "last_result_line",
        "out_dir",
    ]

    rows = [
        summarize_out_dir(
            os.path.abspath(d), contacts_valid_ratio_threshold=args.contacts_valid_ratio_threshold
        )
        for d in args.out_dir
    ]
    rows.sort(key=lambda r: str(r["run_id"]))
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_fmt(row.get(c)) for c in columns])
    print(os.path.abspath(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
