"""Code B Independent Verification: Re-compute metrics from raw evidence.

Reads raw_evidence.jsonl (Code A's raw state snapshots) and independently
re-computes pass/fail metrics. Compares against Code A's RUN_METRICS.json
to detect discrepancies.

This implements the independent verification channel:
  Code A -> raw log/video -> PASS report
  Code B -> raw log independent re-compute -> external criteria -> approve/reject

Physical sanity checks:
  1. grasp=0 && cable_moved -> CONTRADICTION (cable can't move without grip)
  2. cable_z_delta > 0 && no particles near clip XY -> SUSPICIOUS
  3. episode_steps < min_expected -> EARLY_TERMINATION

Usage:
    python thread_isaac_lab/scripts/verify_raw_evidence.py data/newton_clip_routing_XXXXXX/
    python thread_isaac_lab/scripts/verify_raw_evidence.py data/newton_clip_routing_XXXXXX/ --strict
"""

import argparse
import json
import os
import sys

import numpy as np


# ---------------------------------------------------------------------------
# Constants — from task_config SSOT
# ---------------------------------------------------------------------------
_config_dir = os.environ.get(
    "THREAD_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"),
)
if _config_dir not in sys.path:
    sys.path.insert(0, _config_dir)
from task_config import TABLE_HEIGHT, CLIP1_X, CLIP1_Y, CLIP1_Z, CLIP_GROOVE_INNER_RADIUS
CLIP_TOP_Z = CLIP1_Z + 0.030  # 0.830

# Thresholds for independent verification
GRIP_MIN_PARTICLES = 1       # Minimum particles grasped per arm
LIFT_MIN_MM = 5.0            # Minimum cable lift in mm
CLIP_XY_PROXIMITY_MM = CLIP_GROOVE_INNER_RADIUS * 1000  # 6mm (groove inner radius)
MIN_PARTICLES_NEAR_CLIP = 1  # At least 1 particle must be within groove radius


# ---------------------------------------------------------------------------
# Evidence reader
# ---------------------------------------------------------------------------
def load_evidence(evidence_path):
    """Load raw_evidence.jsonl into a list of dicts."""
    events = []
    with open(evidence_path) as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  WARN: Skipping malformed line {line_no}: {e}")
    return events


def load_run_metrics(metrics_path):
    """Load Code A's RUN_METRICS.json."""
    with open(metrics_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Independent re-computation
# ---------------------------------------------------------------------------
def recompute_cable_in_groove(particles, clip_xy, clip_top_z, proximity_mm):
    """Re-compute cable_in_groove from raw particle positions.

    Unlike Code A's check (cable_z_min < clip_top_z only), this also
    verifies XY proximity to the clip.
    """
    if particles is None or len(particles) == 0:
        return {"cable_in_groove": None, "reason": "no_particles"}

    pts = np.array(particles)
    z_vals = pts[:, 2]
    z_min = float(np.min(z_vals))

    # XY distance to clip
    dists_xy = np.linalg.norm(pts[:, :2] - np.array(clip_xy), axis=1)
    min_dist_xy = float(np.min(dists_xy))
    near_clip = int(np.sum(dists_xy < (proximity_mm / 1000.0)))

    # Both conditions: Z below clip top AND XY near clip
    z_ok = z_min < clip_top_z
    xy_ok = near_clip >= MIN_PARTICLES_NEAR_CLIP

    return {
        "cable_in_groove": z_ok and xy_ok,
        "z_min": round(z_min, 4),
        "z_ok": z_ok,
        "clip_top_z": clip_top_z,
        "min_dist_xy_mm": round(min_dist_xy * 1000, 1),
        "particles_near_clip": near_clip,
        "xy_ok": xy_ok,
    }


def check_physical_sanity(episode_events):
    """Run physical sanity checks on an episode's events."""
    violations = []

    p1 = next((e for e in episode_events if e["event"] == "P1_complete"), None)
    p2 = next((e for e in episode_events if e["event"] == "P2_complete"), None)
    p4 = next((e for e in episode_events if e["event"] == "P4_complete"), None)

    if p1 and p2:
        grasped_l = len(p1.get("grasped_left", []))
        grasped_r = len(p1.get("grasped_right", []))
        total_grasped = grasped_l + grasped_r
        cable_z_delta = p2.get("cable_z_delta_mm", 0.0)

        # Check 1: grasp=0 but cable moved
        if total_grasped == 0 and cable_z_delta > 2.0:
            violations.append({
                "check": "grasp_zero_cable_moved",
                "severity": "CRITICAL",
                "detail": f"No particles grasped but cable moved {cable_z_delta:.1f}mm",
                "grasped_total": total_grasped,
                "cable_z_delta_mm": cable_z_delta,
            })

        # Check 2: grasp=0 but P2 reported pass
        if total_grasped == 0 and p2.get("lifted", False):
            violations.append({
                "check": "grasp_zero_lift_pass",
                "severity": "CRITICAL",
                "detail": "No particles grasped but lift reported as passed",
            })

    if p4:
        # Check 3: cable_in_groove but no particles within groove radius
        # Use 6mm groove data if available, fallback to 30mm legacy field
        particles_near = p4.get("particles_in_groove_6mm",
                                p4.get("particles_near_clip_30mm", -1))
        if p4.get("cable_in_groove") and particles_near == 0:
            violations.append({
                "check": "groove_pass_no_xy_proximity",
                "severity": "CRITICAL",
                "detail": "cable_in_groove=True but 0 particles within groove radius (6mm) of clip",
            })

    # Check 4: episode too short (start/end timestamps)
    ep_start = next((e for e in episode_events if e["event"] == "episode_start"), None)
    ep_end = next((e for e in episode_events if e["event"] == "episode_end"), None)
    if ep_start and ep_end:
        duration = ep_end["t"] - ep_start["t"]
        if duration < 1.0:  # Episode < 1 second is suspicious
            violations.append({
                "check": "episode_too_short",
                "severity": "WARNING",
                "detail": f"Episode completed in {duration:.2f}s (< 1.0s minimum)",
            })

    return violations


def compare_with_metrics(episode_events, metrics_episode):
    """Compare Code B's re-computation against Code A's RUN_METRICS."""
    disagreements = []

    p4 = next((e for e in episode_events if e["event"] == "P4_complete"), None)

    if p4 and p4.get("particle_positions"):
        recomputed = recompute_cable_in_groove(
            p4["particle_positions"],
            clip_xy=[CLIP1_X, CLIP1_Y],
            clip_top_z=CLIP_TOP_Z,
            proximity_mm=CLIP_XY_PROXIMITY_MM,
        )

        # Code A's verdict
        code_a_groove = metrics_episode.get("P4_push", {}).get("cable_in_groove")
        code_b_groove = recomputed["cable_in_groove"]

        if code_a_groove != code_b_groove:
            disagreements.append({
                "metric": "cable_in_groove",
                "code_a": code_a_groove,
                "code_b": code_b_groove,
                "reason": recomputed,
            })

    # Compare P2 lift
    p2 = next((e for e in episode_events if e["event"] == "P2_complete"), None)
    if p2:
        # Re-compute from episode_start and P2_complete particle positions
        ep_start = next((e for e in episode_events if e["event"] == "episode_start"), None)
        if ep_start and ep_start.get("particle_positions") and p2.get("particle_positions"):
            z_before = np.mean([p[2] for p in ep_start["particle_positions"]])
            z_after = np.mean([p[2] for p in p2["particle_positions"]])
            recomputed_delta = round((z_after - z_before) * 1000, 2)
            code_a_delta = metrics_episode.get("P2_lift", {}).get("cable_z_delta_mm")

            if code_a_delta is not None:
                diff = abs(recomputed_delta - code_a_delta)
                if diff > 1.0:  # > 1mm discrepancy
                    disagreements.append({
                        "metric": "P2_cable_z_delta_mm",
                        "code_a": code_a_delta,
                        "code_b_recomputed": recomputed_delta,
                        "diff_mm": round(diff, 2),
                    })

    return disagreements


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def verify(run_dir, strict=False):
    """Run independent verification on a run directory."""
    evidence_path = os.path.join(run_dir, "raw_evidence.jsonl")
    metrics_path = os.path.join(run_dir, "RUN_METRICS.json")

    if not os.path.exists(evidence_path):
        print(f"ERROR: {evidence_path} not found")
        print("Code A must generate raw_evidence.jsonl for independent verification.")
        return 1

    if not os.path.exists(metrics_path):
        print(f"ERROR: {metrics_path} not found")
        return 1

    print(f"[VERIFY] Run directory: {run_dir}")
    print(f"[VERIFY] Evidence: {evidence_path}")
    print(f"[VERIFY] Metrics: {metrics_path}")

    events = load_evidence(evidence_path)
    metrics = load_run_metrics(metrics_path)
    print(f"[VERIFY] Loaded {len(events)} evidence events")

    # Group events by episode
    episodes = {}
    current_ep = 0
    for evt in events:
        if evt["event"] == "episode_start":
            current_ep = evt.get("episode", current_ep)
        episodes.setdefault(current_ep, []).append(evt)

    print(f"[VERIFY] Found {len(episodes)} episode(s)")

    overall_pass = True
    all_violations = []
    all_disagreements = []

    for ep_idx in sorted(episodes.keys()):
        ep_events = episodes[ep_idx]
        print(f"\n{'='*50}")
        print(f"  Episode {ep_idx}")
        print(f"{'='*50}")

        # Physical sanity checks
        violations = check_physical_sanity(ep_events)
        all_violations.extend(violations)

        if violations:
            print(f"\n  Physical Sanity Violations:")
            for v in violations:
                marker = "!!!" if v["severity"] == "CRITICAL" else "?"
                print(f"    {marker} [{v['severity']}] {v['check']}: {v['detail']}")
                if v["severity"] == "CRITICAL":
                    overall_pass = False

        # Compare with Code A's metrics
        metrics_ep = None
        if "episodes" in metrics and ep_idx < len(metrics["episodes"]):
            metrics_ep = metrics["episodes"][ep_idx]

        if metrics_ep:
            disagreements = compare_with_metrics(ep_events, metrics_ep)
            all_disagreements.extend(disagreements)

            if disagreements:
                print(f"\n  Metric Disagreements (Code A vs Code B):")
                for d in disagreements:
                    print(f"    DISAGREE: {d['metric']}")
                    print(f"      Code A: {d.get('code_a')}")
                    print(f"      Code B: {d.get('code_b_recomputed', d.get('code_b'))}")
                    if "reason" in d:
                        print(f"      Reason: {d['reason']}")
                    overall_pass = False

        # Independent re-computation of cable_in_groove
        p4 = next((e for e in ep_events if e["event"] == "P4_complete"), None)
        if p4 and p4.get("particle_positions"):
            result = recompute_cable_in_groove(
                p4["particle_positions"],
                clip_xy=[CLIP1_X, CLIP1_Y],
                clip_top_z=CLIP_TOP_Z,
                proximity_mm=CLIP_XY_PROXIMITY_MM,
            )
            print(f"\n  Independent cable_in_groove assessment:")
            print(f"    Z check: z_min={result['z_min']} < clip_top={result['clip_top_z']} -> {result['z_ok']}")
            print(f"    XY check: min_dist={result['min_dist_xy_mm']}mm, "
                  f"particles_near_clip={result['particles_near_clip']} -> {result['xy_ok']}")
            print(f"    Verdict: cable_in_groove={result['cable_in_groove']}")

        if not violations and not (metrics_ep and disagreements):
            print(f"\n  No violations or disagreements found.")

    # Summary
    print(f"\n{'='*50}")
    print(f"  VERIFICATION SUMMARY")
    print(f"{'='*50}")
    print(f"  Physical violations: {len(all_violations)} "
          f"({sum(1 for v in all_violations if v['severity'] == 'CRITICAL')} critical)")
    print(f"  Metric disagreements: {len(all_disagreements)}")
    print(f"  Verdict: {'APPROVE' if overall_pass else 'REJECT'}")

    if strict and not overall_pass:
        print(f"\n  [STRICT MODE] Returning exit code 1")
        return 1

    # Save verification report
    report = {
        "run_dir": run_dir,
        "n_events": len(events),
        "n_episodes": len(episodes),
        "violations": all_violations,
        "disagreements": all_disagreements,
        "verdict": "APPROVE" if overall_pass else "REJECT",
    }
    report_path = os.path.join(run_dir, "VERIFICATION_REPORT.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report: {report_path}")

    return 0 if overall_pass else 1


def main():
    parser = argparse.ArgumentParser(
        description="Code B Independent Verification: re-compute metrics from raw evidence"
    )
    parser.add_argument("run_dir", help="Path to run output directory")
    parser.add_argument("--strict", action="store_true",
                        help="Return non-zero exit code on any violation")
    args = parser.parse_args()

    if not os.path.isdir(args.run_dir):
        print(f"ERROR: {args.run_dir} is not a directory")
        sys.exit(1)

    sys.exit(verify(args.run_dir, strict=args.strict))


if __name__ == "__main__":
    main()
