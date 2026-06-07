#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Per-skill SR baseline 比 sliding-window threshold gate.

Implements hook_spec.md §7.6 + §9.2 — queries Prometheus (or reads a fixture
JSON in --dry-run mode) for per-skill success-rate (SR) over a sliding window,
compares against per-skill baseline, and emits a structured verdict.

Threshold (hook_spec.md §9.2 + §9.4):
  delta_pct ≥ -5%       → PASS
  -5% > delta_pct ≥ -10% → WARNING (Slack only, no auto-action)
  -10% > delta_pct ≥ -15% → CRITICAL (RP3 hook disable + on-call)
  delta_pct < -15%      → PAGE (RP3 + RC4 + immediate page)

Exit codes (dispatcher contract):
  0 = PASS / WARNING (proceed, log only)
  3 = FAIL_SR (CRITICAL or PAGE — auto-rollback + RP3/RC4)
  4 = FAIL_INFRA (Prometheus unreachable, etc.)
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

EXIT_PASS = 0
EXIT_FAIL_SR = 3
EXIT_FAIL_INFRA = 4

SKILLS = ("skill_ac", "skill_ic", "skill_ar", "skill_grip_clamp")
WARNING_THRESHOLD = -5.0
CRITICAL_THRESHOLD = -10.0
PAGE_THRESHOLD = -15.0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Per-skill SR threshold gate.")
    p.add_argument("--query-window", default="24h", help="Sliding window (e.g., 24h)")
    p.add_argument("--threshold-warning", type=float, default=WARNING_THRESHOLD)
    p.add_argument("--threshold-critical", type=float, default=CRITICAL_THRESHOLD)
    p.add_argument("--threshold-page", type=float, default=PAGE_THRESHOLD)
    p.add_argument("--current-stage", default=None, help="Canary stage 10/50/100 (advisory)")
    p.add_argument("--next-stage", default=None, help="Next canary stage (advisory)")
    p.add_argument("--steady-state-mode", action="store_true", help="Stage 4 mode")
    p.add_argument("--audit-id", default=None)
    p.add_argument("--ts", default=None)
    p.add_argument("--output-json", required=True, type=Path)
    p.add_argument(
        "--fixture-json",
        type=Path,
        default=None,
        help="In dry-run mode, read SR fixture from this JSON instead of Prometheus",
    )
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def load_fixture(path: Path | None) -> dict[str, dict[str, float]]:
    """Return {skill: {current, baseline, delta_pct}} from fixture.

    Default fixture (no path) = all 4 skills at 0% delta (PASS scenario).
    """
    if path is None or not path.exists():
        return {s: {"current": 0.86, "baseline": 0.86, "delta_pct": 0.0} for s in SKILLS}
    raw = json.loads(path.read_text())
    out: dict[str, dict[str, float]] = {}
    for s in SKILLS:
        rec = raw.get(s, {"current": 0.86, "baseline": 0.86})
        cur = float(rec.get("current", 0.86))
        base = float(rec.get("baseline", 0.86))
        delta = ((cur - base) / base * 100.0) if base else 0.0
        out[s] = {"current": cur, "baseline": base, "delta_pct": round(delta, 3)}
    return out


def query_prometheus(skill: str, window: str) -> tuple[float, float]:
    """Real implementation would call PROMETHEUS_URL. Stub raises to force --dry-run."""
    raise RuntimeError("Prometheus integration is production-only; use --dry-run for local verify")


def classify(per_skill: dict[str, dict[str, float]], warn: float, crit: float, page: float) -> tuple[str, str]:
    """Return (verdict, alarm_action)."""
    worst_delta = min(rec["delta_pct"] for rec in per_skill.values())
    if worst_delta < page:
        return "PAGE", "RP3+RC4"
    if worst_delta < crit:
        return "CRITICAL", "RP3+canary_stage_rollback"
    if worst_delta < warn:
        return "WARNING", "NONE"
    return "PASS", "NONE"


def main() -> int:
    args = parse_args()
    audit_id = args.audit_id or str(uuid.uuid4())
    ts = args.ts or datetime.now(timezone.utc).isoformat()

    try:
        if args.dry_run:
            per_skill = load_fixture(args.fixture_json)
        else:
            per_skill = {}
            for s in SKILLS:
                cur, base = query_prometheus(s, args.query_window)
                delta = ((cur - base) / base * 100.0) if base else 0.0
                per_skill[s] = {"current": cur, "baseline": base, "delta_pct": round(delta, 3)}
    except Exception as exc:
        payload = {
            "stage": "per-canary-stage" if not args.steady_state_mode else "steady-state",
            "ts": ts, "audit_id": audit_id,
            "per_skill_sr": {"verdict": "FAIL_INFRA", "error": str(exc)},
            "overall_verdict": "FAIL", "exit_code": EXIT_FAIL_INFRA, "alarm_action": "RC4",
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, indent=2))
        print(f"[FAIL_INFRA] SR query failed: {exc}", file=sys.stderr)
        return EXIT_FAIL_INFRA

    verdict, alarm = classify(per_skill, args.threshold_warning, args.threshold_critical, args.threshold_page)
    exit_code = EXIT_PASS if verdict in ("PASS", "WARNING") else EXIT_FAIL_SR
    payload = {
        "stage": "steady-state" if args.steady_state_mode else "per-canary-stage",
        "ts": ts, "audit_id": audit_id,
        "git_diff": {"verdict": "SKIP"},
        "cluster_g_test": {"verdict": "SKIP"},
        "per_skill_sr": {**per_skill, "verdict": verdict},
        "overall_verdict": "PASS" if exit_code == EXIT_PASS else "FAIL",
        "exit_code": exit_code, "alarm_action": alarm,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2))
    print(f"[{verdict}] SR audit_id={audit_id} alarm={alarm}", file=sys.stderr if exit_code else sys.stdout)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
