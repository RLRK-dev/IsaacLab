# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Connect original-FK B task branches with simultaneously checked free arms [m, rad, s]."""

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_split_b_plan import digest
from op030_split_b_stagger_v06 import build_sequence_final
from op030_split_b_stagger_v06_plan import DEFAULT_MESH, Candidate
from op030_split_b_v04 import load
from op030_split_wire_motion import WirePlacementConfig, target_checks
from replay_op030_motion import path_sample, path_timing


class ConnectedCandidate(Candidate):
    """Use retained constrained IK and one 12D check for both free arms [rad]."""

    def __init__(self, survey: str, mesh: Path, h1_yaw_bias_degrees: float = 0.0):
        metadata = json.loads((ROOT / "audit" / (survey + ".json")).read_text())
        variant = {
            key: metadata[key]
            for key in (
                "work_yaw_degrees",
                "grasp_side_flip",
                "orbit_y_m",
                "overbody",
                "swap_roles",
                "bend_during_turn",
            )
            if key in metadata
        }
        variant["h1_yaw_bias_degrees"] = h1_yaw_bias_degrees
        super().__init__(mesh, survey=survey, config=WirePlacementConfig(**metadata["config"]), **variant)
        self.variant = variant
        self.branches = load(ROOT / "analysis" / (survey + ".npz"))
        self.selected = {
            (2, 0): "section_0_branch_0",
            (2, 1): "section_2_branch_0",
            (1, 0): "section_1_branch_0",
            (1, 1): "section_3_branch_1",
        }
        self.initial_t, self.initial_q = self.old["author_times"], self.old["joints"]
        self.blocks = []
        self.free_paths, self.combined_free = {}, {}

    def reuse_constraints(self, prefix: str, *, compact: bool = True) -> dict:
        """Reuse solved joint samples with an exact phase time map [rad, s]."""
        path = ROOT / "analysis" / (prefix + ".npz")
        report_path = ROOT / "audit" / (prefix + ".json")
        record = json.loads(report_path.read_text())
        if digest(path) != record["output_sha256"] or record["failures"]:
            raise ValueError("Constrained source changed or contains IK failures")
        if record["variant"] != self.variant:
            raise ValueError("Constrained source variant differs")
        old_sequence = self.sequence
        if compact:
            self.sequence = build_sequence_final(self.sequence.config)
            self.screen.sequence = self.sequence
        data = load(path)
        times, joints, source_times = [], [], []
        maximum_target_error = 0.0
        for phase in self.sequence.phases:
            begin = phase["legacy_start"] if compact else phase["start"]
            end = phase["legacy_stop"] if compact else phase["stop"]
            selected = np.flatnonzero((data["times"] >= begin - 1e-8) & (data["times"] <= end + 1e-8))
            for index in selected:
                source_time = float(data["times"][index])
                time = float(phase["start"] + source_time - begin)
                for boundary in (phase["start"], phase["stop"]):
                    if abs(time - boundary) < 1e-8:
                        time = float(boundary)
                if times and time <= times[-1] + 1e-8:
                    continue
                original = old_sequence.evaluate(source_time)
                target = self.sequence.evaluate(time)
                for key in ("tools", "grips", "root", "product_pose"):
                    maximum_target_error = max(
                        maximum_target_error, float(np.max(abs(np.asarray(original[key]) - np.asarray(target[key]))))
                    )
                for uid in target["wires"]:
                    maximum_target_error = max(
                        maximum_target_error,
                        float(
                            np.max(
                                abs(
                                    original["wires"][uid]["shape"].centerline
                                    - target["wires"][uid]["shape"].centerline
                                )
                            )
                        ),
                    )
                times.append(time)
                source_times.append(source_time)
                joints.append(data["joints"][index])
        if maximum_target_error > 1e-8:
            raise ValueError(f"Time compaction changed a target: {maximum_target_error}")
        self.times, self.q = np.array(times), np.array(joints)
        self.source_times = np.array(source_times)
        return dict(
            source_npz=str(path.relative_to(ROOT)),
            source_sha256=digest(path),
            source_report_sha256=digest(report_path),
            samples=len(times),
            maximum_target_error=maximum_target_error,
            removed_author_intervals_s=self.sequence.removed_intervals if compact else [],
            ik_reused_without_search=True,
        )

    def at(self, time: float) -> np.ndarray:
        """Return constrained interpolation or the exact checked free polyline [rad, s]."""
        phase_index = self.sequence.evaluate(time)["phase_index"]
        if phase_index in self.combined_free:
            phase = self.sequence.phases[phase_index]
            record = self.combined_free[phase_index]
            u = float(np.clip((time - phase["start"]) / (phase["stop"] - phase["start"]), 0, 1))
            return path_sample(record["points"].reshape(-1, 12), record["knots"], u).reshape(2, 6)
        return super().at(time)

    def constrained_check(self, reused: dict | None = None) -> dict:
        """Screen every solved simultaneous constrained state against actual meshes [s]."""
        constraints = self.constraints(step=0.1) if reused is None else reused
        if self.failures:
            return dict(constraints=constraints, hits=[], checked=0)
        hits, checked = [], 0
        for index, time in enumerate(self.times):
            state = self.sequence.evaluate(float(time))
            if any(state["free_hands"]) or not np.isfinite(self.q[index]).all():
                continue
            pairs = self.score_all(state, self.q[index])
            if pairs:
                hits.append(dict(time_s=float(time), phase=state["phase_index"], label=state["label"], pairs=pairs))
            checked += 1
        return dict(constraints=constraints, hits=hits, checked=checked)

    def free_connect(self) -> list:
        """Connect each simultaneous empty-hand interval in original joint limits [rad, s]."""
        from op030_b_stagger_free_12d import plan_free_path_12d

        records = []
        for index, phase in enumerate(self.sequence.phases):
            if not any(phase["free_hands"]):
                continue
            if not all(phase["free_hands"]):
                raise ValueError("Unexpected unilateral phase; simultaneous contract must be explicit")
            start = super().at(phase["start"])
            stop = super().at(phase["stop"])
            target = self.sequence.evaluate(phase["stop"] - 1e-8)
            if np.max(abs(self.sequence.evaluate(phase["start"])["root"] - target["root"])) > 1e-8:
                raise ValueError("A changing torso requires a time-aware transit, not a static free checker")
            points, audit = plan_free_path_12d(start, stop, lambda q: 10.0 * len(self.score_all(target, q)))
            records.append(dict(phase_index=index, label=phase["label"], found=points is not None, audit=audit))
            print("STAGGER_FREE_CONNECT", index, points is not None, flush=True)
            if points is None:
                self.failures.append(dict(kind="free_12d", phase_index=index, audit=audit))
                break
            self.combined_free[index] = dict(
                points=points, knots=path_timing(points.reshape(-1, 12), 1.2 * 0.9, 2.0 * 0.9)
            )
            # The route solver has no time coordinate. If the free approach
            # also narrows the fingers, validate the actual gap along the
            # resulting stopped-quintic time law instead of treating the
            # final gap as a proof for the whole path.
            timed_hits, samples = [], 0
            if np.max(abs(phase["before"]["gaps"] - phase["after"]["gaps"])) > 1e-12:
                knots = self.combined_free[index]["knots"]
                for segment in range(len(points) - 1):
                    count = max(
                        2, int(np.ceil(1.875 * np.max(abs(points[segment + 1] - points[segment])) / 0.0025)) + 1
                    )
                    for local_time in np.linspace(0, 1, count):
                        fraction = (knots[segment] + local_time * (knots[segment + 1] - knots[segment])) / knots[-1]
                        author = phase["start"] + fraction * (phase["stop"] - phase["start"])
                        actual_target = self.sequence.evaluate(float(author))
                        actual_q = path_sample(points.reshape(-1, 12), knots, fraction).reshape(2, 6)
                        pairs = self.score_all(actual_target, actual_q)
                        samples += 1
                        if pairs:
                            timed_hits.append(dict(author_time_s=float(author), pairs=pairs))
            records[-1]["time_varying_grip_check"] = dict(
                samples=samples,
                hits=timed_hits,
                maximum_joint_step_rad=0.0025,
                constant_grip_already_checked=not samples,
            )
            if timed_hits:
                self.failures.append(dict(kind="free_12d_time_varying_grip", phase_index=index, hits=timed_hits))
                break
        return records


def main() -> None:
    """Save a separate candidate connection, retaining all failed evidence [m, rad, s]."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--survey", default="op030_split_b_stagger_v06_survey_09")
    parser.add_argument("--mesh", type=Path, default=DEFAULT_MESH)
    parser.add_argument("--h1_yaw_bias_degrees", type=float, default=0.0)
    parser.add_argument("--output", required=True)
    parser.add_argument("--reuse_constraints")
    args = parser.parse_args()
    output = ROOT / "analysis" / (args.output + ".npz")
    audit = ROOT / "audit" / (args.output + ".json")
    if output.exists() or audit.exists():
        raise FileExistsError(output)
    candidate = ConnectedCandidate(args.survey, args.mesh, args.h1_yaw_bias_degrees)
    reused = candidate.reuse_constraints(args.reuse_constraints) if args.reuse_constraints else None
    report = candidate.constrained_check(reused)
    free = []
    if not candidate.failures and not report["hits"]:
        free = candidate.free_connect()
    arrays = dict(times=candidate.times, joints=candidate.q)
    if reused:
        arrays["source_author_times"] = candidate.source_times
    for index, record in candidate.combined_free.items():
        arrays[f"free_{index}_points"] = record["points"]
        arrays[f"free_{index}_knots"] = record["knots"]
    np.savez_compressed(output, **arrays)
    result = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        config=asdict(candidate.sequence.config),
        variant=candidate.variant,
        phases=[{key: p[key] for key in ("label", "start", "stop")} for p in candidate.sequence.phases],
        survey=args.survey,
        mesh=str(args.mesh.relative_to(ROOT)) if args.mesh.is_absolute() else str(args.mesh),
        mesh_sha256=digest(args.mesh),
        target_checks=target_checks(candidate.sequence),
        constraints=report,
        free=free,
        failures=candidate.failures,
        passed=not candidate.failures and not report["hits"],
        output_sha256=digest(output),
        formal_physical_verdict=None,
    )
    audit.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("STAGGER_CONNECTION_COMPLETE", result["passed"], len(report["hits"]), len(candidate.failures), flush=True)


if __name__ == "__main__":
    main()
