#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fcntl


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False, dir=str(path.parent), prefix=f"{path.name}.", suffix=".tmp"
    ) as tf:
        json.dump(data, tf, ensure_ascii=False, indent=2, sort_keys=True)
        tf.flush()
        os.fsync(tf.fileno())
        tmp_name = tf.name
    os.replace(tmp_name, path)


def _load_json_or_empty(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@dataclass
class ContractConfig:
    objective_id: str
    metric_name: str
    direction: str
    epsilon: float = 1e-6
    max_stagnation_steps: int = 30


class SSOTTrajectoryContract:
    def __init__(self, run_summary_path: str, lock_path: str, cfg: ContractConfig) -> None:
        self.run_summary_path = Path(run_summary_path)
        self.lock_path = Path(lock_path)
        self.cfg = cfg
        if cfg.direction not in ("decrease", "increase"):
            raise ValueError("direction must be 'decrease' or 'increase'")

    def _with_lock(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        f = self.lock_path.open("a+", encoding="utf-8")
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        return f

    def _ensure_contract(self, rs: dict[str, Any]) -> dict[str, Any]:
        c = rs.get("trajectory_contract_v1")
        if not isinstance(c, dict):
            c = {}
            rs["trajectory_contract_v1"] = c

        pm = c.get("progress_metric")
        if not isinstance(pm, dict):
            pm = {}
            c["progress_metric"] = pm
        pm.setdefault("name", self.cfg.metric_name)
        pm.setdefault("direction", self.cfg.direction)
        pm.setdefault("epsilon", float(self.cfg.epsilon))
        pm.setdefault("baseline", None)
        pm.setdefault("last", None)
        pm.setdefault("best", None)
        pm.setdefault("samples", 0)
        pm.setdefault("improve_count", 0)
        pm.setdefault("improvement_abs", 0.0)
        pm.setdefault("has_material_improvement", False)
        pm.setdefault("stagnation_steps", 0)
        pm.setdefault("max_stagnation_steps", int(self.cfg.max_stagnation_steps))
        pm.setdefault("last_improve_step", None)

        pl = c.get("planning")
        if not isinstance(pl, dict):
            pl = {}
            c["planning"] = pl
        pl.setdefault("planner_cycle_count", 0)
        pl.setdefault("plan_revision_count", 0)
        pl.setdefault("last_plan_revision_step", None)

        cs = c.get("constraints")
        if not isinstance(cs, dict):
            cs = {}
            c["constraints"] = cs
        cs.setdefault("hard_ok", True)
        cs.setdefault("violation_count", 0)
        cs.setdefault("last_violation", None)

        fb = c.get("fallback")
        if not isinstance(fb, dict):
            fb = {}
            c["fallback"] = fb
        fb.setdefault("mode", "NONE")
        fb.setdefault("reason", None)
        fb.setdefault("ts", None)

        c.setdefault("objective_id", self.cfg.objective_id)
        c["last_update_ts"] = _utc_now_iso()
        return rs

    def _is_improvement(self, old_best: float, new_val: float) -> bool:
        eps = float(self.cfg.epsilon)
        if self.cfg.direction == "decrease":
            return new_val < (old_best - eps)
        return new_val > (old_best + eps)

    # -- ActiveRun.json stale-entry cleanup --------------------------------

    _ACTIVE_RUN_PATH = Path("/home/rlrk/Claudecode/shared/ActiveRun.json")

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        """Return True if *pid* is running (signal-0 probe)."""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError, PermissionError):
            return False

    def _cleanup_active_run(self) -> int:
        """Remove stale entries from ActiveRun.json.  Returns count removed."""
        ar_path = self._ACTIVE_RUN_PATH
        if not ar_path.exists():
            return 0
        data = _load_json_or_empty(ar_path)
        tests = data.get("active_tests")
        if not isinstance(tests, list):
            return 0
        original = len(tests)
        kept: list[dict[str, Any]] = []
        for entry in tests:
            pid = entry.get("pid")
            if pid is None:
                # pid=null → process already gone, remove
                continue
            if isinstance(pid, int) and not self._pid_alive(pid):
                continue
            kept.append(entry)
        removed = original - len(kept)
        if removed > 0:
            data["active_tests"] = kept
            data["last_updated"] = _utc_now_iso()
            _atomic_write_json(ar_path, data)
            print(f"[CONTRACT] ActiveRun cleanup: removed {removed} stale entries ({original} -> {len(kept)})")
        return removed

    # -- reset --------------------------------------------------------------

    def reset(self, *, run_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        """Reset the trajectory contract for a new run.

        Clears stagnation counters, progress metrics, and fallback state
        so that a fresh run does not inherit stale state from a previous run.

        If *run_meta* is provided, top-level RUN_SUMMARY fields (run_id,
        out_dir, log_path, pid, process_alive, …) are overwritten so that
        downstream consumers (generate_run_metrics.sh, validators) see the
        correct values from the very start of the new run.
        """
        lockf = self._with_lock()
        try:
            # 1. ActiveRun.json stale-entry cleanup
            self._cleanup_active_run()

            # 2. RUN_SUMMARY reset
            rs = _load_json_or_empty(self.run_summary_path)

            # 2a. Apply run_meta top-level fields (run_id, out_dir, log_path, …)
            if run_meta:
                for key, val in run_meta.items():
                    rs[key] = val
                print(f"[CONTRACT] Reset top-level RUN_SUMMARY fields: {sorted(run_meta.keys())}")

            # 2b. Remove old contract entirely so _ensure_contract re-initialises
            rs.pop("trajectory_contract_v1", None)
            rs = self._ensure_contract(rs)
            c = rs["trajectory_contract_v1"]
            c["last_update_ts"] = _utc_now_iso()
            _atomic_write_json(self.run_summary_path, rs)
            print(f"[CONTRACT] Reset trajectory_contract_v1 for new run (objective={self.cfg.objective_id})")
            return c
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
            lockf.close()

    def report_progress(self, *, step: int, value: float) -> dict[str, Any]:
        lockf = self._with_lock()
        try:
            rs = self._ensure_contract(_load_json_or_empty(self.run_summary_path))
            c = rs["trajectory_contract_v1"]
            pm = c["progress_metric"]

            pm["samples"] = int(pm.get("samples", 0)) + 1
            pm["last"] = float(value)
            if pm["baseline"] is None:
                pm["baseline"] = float(value)

            if pm["best"] is None:
                pm["best"] = float(value)
                pm["last_improve_step"] = int(step)
                pm["improve_count"] = int(pm.get("improve_count", 0)) + 1
                pm["stagnation_steps"] = 0
            else:
                old_best = float(pm["best"])
                if self._is_improvement(old_best, float(value)):
                    pm["best"] = float(value)
                    pm["last_improve_step"] = int(step)
                    pm["improve_count"] = int(pm.get("improve_count", 0)) + 1
                    pm["stagnation_steps"] = 0
                else:
                    pm["stagnation_steps"] = int(pm.get("stagnation_steps", 0)) + 1

            baseline = pm.get("baseline")
            best = pm.get("best")
            eps = float(pm.get("epsilon", self.cfg.epsilon))
            if baseline is not None and best is not None:
                baseline_f = float(baseline)
                best_f = float(best)
                if self.cfg.direction == "decrease":
                    improvement_abs = baseline_f - best_f
                else:
                    improvement_abs = best_f - baseline_f
                pm["improvement_abs"] = float(improvement_abs)
                pm["has_material_improvement"] = bool(improvement_abs > eps)

            pl = c["planning"]
            pl["planner_cycle_count"] = int(pl.get("planner_cycle_count", 0)) + 1
            c["last_update_ts"] = _utc_now_iso()
            _atomic_write_json(self.run_summary_path, rs)
            return c
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
            lockf.close()

    def report_plan_revision(self, *, step: int) -> dict[str, Any]:
        lockf = self._with_lock()
        try:
            rs = self._ensure_contract(_load_json_or_empty(self.run_summary_path))
            c = rs["trajectory_contract_v1"]
            pl = c["planning"]
            pl["plan_revision_count"] = int(pl.get("plan_revision_count", 0)) + 1
            pl["last_plan_revision_step"] = int(step)
            c["last_update_ts"] = _utc_now_iso()
            _atomic_write_json(self.run_summary_path, rs)
            return c
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
            lockf.close()

    def record_constraint_violation(self, *, step: int, code: str, detail: str) -> dict[str, Any]:
        lockf = self._with_lock()
        try:
            rs = self._ensure_contract(_load_json_or_empty(self.run_summary_path))
            c = rs["trajectory_contract_v1"]
            cs = c["constraints"]
            cs["hard_ok"] = False
            cs["violation_count"] = int(cs.get("violation_count", 0)) + 1
            cs["last_violation"] = {
                "ts": _utc_now_iso(),
                "step": int(step),
                "code": str(code),
                "detail": str(detail),
            }
            c["last_update_ts"] = _utc_now_iso()
            _atomic_write_json(self.run_summary_path, rs)
            return c
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
            lockf.close()

    def set_fallback(self, *, mode: str, reason: str) -> dict[str, Any]:
        lockf = self._with_lock()
        try:
            rs = self._ensure_contract(_load_json_or_empty(self.run_summary_path))
            c = rs["trajectory_contract_v1"]
            fb = c["fallback"]
            fb["mode"] = str(mode)
            fb["reason"] = str(reason)
            fb["ts"] = _utc_now_iso()
            c["last_update_ts"] = _utc_now_iso()
            _atomic_write_json(self.run_summary_path, rs)
            return c
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
            lockf.close()

    def snapshot(self) -> dict[str, Any] | None:
        lockf = self._with_lock()
        try:
            rs = _load_json_or_empty(self.run_summary_path)
            c = rs.get("trajectory_contract_v1")
            return c if isinstance(c, dict) else None
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
            lockf.close()
