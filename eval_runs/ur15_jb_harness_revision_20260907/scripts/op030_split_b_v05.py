# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Synchronize B supply approach and seated-wire vertical release [m, rad, s].

The v04 trajectory is immutable. This candidate retains its unchanged samples,
uses its saved free polylines with a shared clock, and solves only new release
and retreat intervals. Triangle checks are auxiliary, not a physical verdict.
"""

import argparse
import json
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import LIMITS
from op030_split_b_check import SplitBMeshes
from op030_split_b_plan import Planner, digest
from op030_split_b_v04 import load
from op030_split_wire_motion import WirePlacementConfig, WirePlacementSequence
from replay_op030_motion import path_sample, path_timing
from solve_op030_motion import capture_robots

SOURCE_BANK = ROOT / "data/op030_split_b_motion_v04.npz"
SOURCE_AUDIT = ROOT / "audit/op030_split_b_motion_v04.json"
SOURCE_CONNECTION = ROOT / "analysis/op030_split_b_top_entry_clip_v03_connection.npz"
DEFAULT_MESH = ROOT / "data/op030_split_b_parallel_v05_meshes.npz"


def build_sequence(config: WirePlacementConfig | None = None) -> WirePlacementSequence:
    """Build the separate v05 target schedule using v04 dimensions [m, s]."""
    config = config or WirePlacementConfig(**json.loads(SOURCE_AUDIT.read_text())["config"])
    if config.transport_clips:
        raise ValueError("The v05 variant requires the removed-clip configuration")
    old = WirePlacementSequence(config)
    result = deepcopy(old)
    result.phases, result.time = [], 0.0
    result.source_phases, result.phase_kinds = [], []
    skip = set()
    for index, phase in enumerate(old.phases):
        if index in skip:
            continue
        if phase["label"] in ("H03-2／右指を開く", "H03-1／左指を開く"):
            number = 2 if "H03-2" in phase["label"] else 1
            uid = old.active_uids[number]
            seated = old.evaluate(phase["start"])
            result.state = deepcopy(phase["before"])
            result.state["hands"] = list(seated["hands"].copy())
            result.state["holds"] = {}
            result.state["supports"][uid] = "J1_stud_and_T_saddle"
            gaps = [config.release_gap, config.h1_release_gap if number == 1 else config.release_gap]
            result.phase(f"H03-{number}／両指を同時に開く", 1.0, gaps=gaps)
            hands = [hand.copy() for hand in result.state["hands"]]
            for hand in hands:
                hand[2, 3] += 0.180
            result.phase(f"H03-{number}／両腕を同時に180mm鉛直上昇", 3.0, hands=hands)
            result.phase(f"H03-{number}／離隔後に両指を全開", 1.0, gaps=[0.080, 0.080])
            park = old.phases[index + 4]
            assert "両腕待機位置へ" in park["label"]
            result.phase(park["label"], 5.0, hands=park["after"]["hands"], free=[True, True])
            result.source_phases.extend([None, None, None, index + 4])
            result.phase_kinds.extend(["release", "vertical", "open_clear", "park"])
            skip.update(range(index + 1, index + 5))
        else:
            current = deepcopy(phase)
            duration = phase["stop"] - phase["start"]
            current.update(start=result.time, stop=result.time + duration)
            result.phases.append(current)
            result.time += duration
            result.state = deepcopy(current["after"])
            result.source_phases.append(index)
            result.phase_kinds.append("approach" if "両指を両端の被覆上方へ" in phase["label"] else "reuse")
    return result


class Candidate(Planner):
    """Reuse proven FK/checkers for the finite simultaneous candidate [m, rad]."""

    def __init__(self, mesh: Path):
        self.mesh = mesh.resolve()
        self.metadata = json.loads(SOURCE_AUDIT.read_text())
        self.old = load(SOURCE_BANK)
        if digest(SOURCE_BANK) != self.metadata["output_sha256"]:
            raise ValueError("Immutable source bank changed")
        self.sequence = build_sequence(WirePlacementConfig(**self.metadata["config"]))
        self.screen = SplitBMeshes(self.sequence, self.mesh)
        self.robots = capture_robots()
        self.start_state = self.sequence.evaluate(0.0)
        self.support_contacts, self.failures, self.records = [], [], []
        self.blocks = {}
        self.extra = tuple(
            uid + suffix for uid in self.sequence.active_uids.values() for suffix in ("_J1", "_T", "_insulation")
        )
        connection_config = self.metadata["config"] | {"transport_clips": True}
        connection_sequence = WirePlacementSequence(WirePlacementConfig(**connection_config))
        self.connection_phases = {p["label"]: i for i, p in enumerate(connection_sequence.phases)}
        self.connection = load(SOURCE_CONNECTION)

    def score_all(self, target: dict, joints: np.ndarray) -> list:
        """Check both contemporaneous arms and both placed/held wires [m, rad]."""
        _, pairs = self.score(target, joints)
        self.screen.score(0, self.extra)
        pairs = set(map(tuple, pairs)) | set(map(tuple, self.screen.last_pairs))
        allowed = set()
        for row in self.sequence.rows:
            uid = row["uid"]
            if (
                uid in self.sequence.active_uids.values()
                and np.max(
                    abs(target["wires"][uid]["shape"].centerline - self.start_state["wires"][uid]["shape"].centerline)
                )
                < 1e-10
            ):
                allowed.update(
                    frozenset((f"OP030B_wire_supply_row{row['row']:02d}_saddle{k}", uid + "_insulation"))
                    for k in (0, 1)
                )
        return [p for p in sorted(pairs) if frozenset(p) not in allowed]

    def old_indices(self, source_phase: int) -> np.ndarray:
        """Return original inclusive phase frame indices."""
        phase = self.metadata["phases"][source_phase]
        return np.arange(round(phase["start"] * 30), round(phase["stop"] * 30) + 1)

    def path_records(self, label: str) -> list:
        """Read existing screened free polylines without repeating a search [rad]."""
        index = self.connection_phases[label]
        records = []
        for order in (0, 1):
            stem = f"free_{index}_{order}_"
            points = self.connection[stem + "points"]
            records.append(
                dict(
                    arm=int(self.connection[stem + "arm"]),
                    points=points,
                    knots=path_timing(points, 1.2 * 0.9, 2.0 * 0.9),
                )
            )
        return records

    def constrained(self, index: int, seed: np.ndarray) -> dict:
        """Solve one new simultaneous target phase continuously [m, rad, s]."""
        phase = self.sequence.phases[index]
        times = np.linspace(phase["start"], phase["stop"], 91)
        joints, maximum = [], 0.0
        for time in times:
            current = seed.copy()
            for arm in (0, 1):
                current[arm], residual = self.solve(float(time), arm, seed[arm])
                maximum = max(maximum, float(residual))
                if (
                    residual > 1e-5
                    or np.max(abs(current[arm] - seed[arm])) > 0.8
                    or np.any(abs(current[arm]) >= LIMITS)
                ):
                    self.failures.append(
                        dict(
                            kind="continuous_ik",
                            phase=index,
                            time=float(time),
                            arm=arm,
                            residual=float(residual),
                            delta=float(np.max(abs(current[arm] - seed[arm]))),
                        )
                    )
                    return {}
            target = self.sequence.evaluate(float(time))
            hits = self.score_all(target, current)
            if hits:
                self.failures.append(dict(kind="new_phase_mesh", phase=index, time=float(time), pairs=hits))
                return {}
            joints.append(current.copy())
            seed = current
        joints = np.array(joints)
        velocity = np.gradient(joints, times, axis=0, edge_order=2)
        acceleration = np.gradient(velocity, times, axis=0, edge_order=2)
        factor = max(1.0, 1.4 * float(abs(velocity).max()) / 1.2, np.sqrt(1.4 * float(abs(acceleration).max()) / 2.0))
        duration = np.ceil((phase["stop"] - phase["start"]) * factor * 30) / 30
        return dict(times=times, joints=joints, duration=float(duration), maximum_residual=maximum)

    def park(self, index: int, start: np.ndarray, goal: np.ndarray) -> dict:
        """Reconnect the raised empty hands to the retained park in finite arm orders [rad]."""
        from op030_free_paths import plan_free_path

        phase = self.sequence.phases[index]
        target = self.sequence.evaluate(phase["stop"] - 1e-9)
        attempts = []
        for order in ((0, 1), (1, 0)):
            current, paths = start.copy(), []
            for arm in order:
                initial = self.score_all(target, current)
                if initial:
                    attempts.append(dict(order=order, arm=arm, start_pairs=initial))
                    break
                fixed = current.copy()

                def cost(q, arm=arm, fixed=fixed):
                    both = fixed.copy()
                    both[arm] = q
                    return 10.0 * len(self.score_all(target, both))

                points = plan_free_path(current[arm], goal[arm], cost)
                attempts.append(dict(order=order, arm=arm, found=points is not None, detail=plan_free_path.last_debug))
                if points is None:
                    break
                knots = path_timing(points, 1.2 * 0.9, 2.0 * 0.9)
                paths.append(dict(arm=arm, points=points, knots=knots))
                current[arm] = goal[arm]
            else:
                duration = np.ceil(sum(p["knots"][-1] for p in paths) * 30) / 30
                return dict(paths=paths, duration=float(duration), attempts=attempts)
        self.failures.append(dict(kind="new_park_connection", phase=index, attempts=attempts))
        return {}

    def prepare(self) -> None:
        """Screen just the explicit changed windows before producing a full bank [s]."""
        previous = self.old["joints"][0].copy()
        for index, (phase, kind, source) in enumerate(
            zip(self.sequence.phases, self.sequence.phase_kinds, self.sequence.source_phases, strict=True)
        ):
            if kind == "reuse":
                frames = self.old_indices(source)
                block = dict(source_indices=frames, duration=(len(frames) - 1) / 30, joints=self.old["joints"][frames])
            elif kind == "approach":
                paths = self.path_records(phase["label"])
                duration = np.ceil(max(p["knots"][-1] for p in paths) * 30) / 30
                block = dict(paths=paths, duration=float(duration))
                for u in np.linspace(0, 1, round(duration * 30) + 1):
                    q = previous.copy()
                    for record in paths:
                        q[record["arm"]] = path_sample(record["points"], record["knots"], u)
                    target = self.sequence.evaluate(float(phase["start"] + u * (phase["stop"] - phase["start"])))
                    hits = self.score_all(target, q)
                    if hits:
                        self.failures.append(
                            dict(kind="synchronous_approach_mesh", phase=index, u=float(u), pairs=hits)
                        )
                        break
                block["joints"] = np.array([previous, q])
            elif kind == "park":
                goal = self.old["joints"][self.old_indices(source)[-1]]
                block = self.park(index, previous, goal)
                if block:
                    block["joints"] = np.array([previous, goal])
            else:
                block = self.constrained(index, previous)
            print("B_V05_PHASE", index, kind, phase["label"], block.get("duration"), len(self.failures), flush=True)
            if self.failures:
                return
            previous = block["joints"][-1].copy()
            self.blocks[index] = block
            self.records.append(
                dict(
                    phase_index=index,
                    kind=kind,
                    source_phase=source,
                    label=phase["label"],
                    duration_s=block["duration"],
                    maximum_residual=block.get("maximum_residual"),
                    attempts=block.get("attempts"),
                )
            )


def main() -> None:
    """Write a non-overwriting finite candidate diagnostic [m, rad, s]."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh", type=Path, default=DEFAULT_MESH)
    parser.add_argument("--output", default="op030_split_b_parallel_v05_probe")
    args = parser.parse_args()
    report_path = ROOT / "audit" / (args.output + ".json")
    array_path = ROOT / "analysis" / (args.output + ".npz")
    if report_path.exists() or array_path.exists():
        raise FileExistsError(report_path)
    candidate = Candidate(args.mesh)
    candidate.prepare()
    arrays, blocks = {}, {}
    for index, block in candidate.blocks.items():
        info = {key: value for key, value in block.items() if key in ("duration", "maximum_residual")}
        for key in ("times", "joints", "source_indices"):
            if key in block:
                arrays[f"phase_{index}_{key}"] = block[key]
        if "paths" in block:
            info["paths"] = []
            for order, path in enumerate(block["paths"]):
                info["paths"].append(dict(arm=path["arm"], order=order))
                for key in ("points", "knots"):
                    arrays[f"phase_{index}_path_{order}_{key}"] = path[key]
        blocks[index] = info
    np.savez_compressed(array_path, **arrays)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        config=asdict(candidate.sequence.config),
        factory="op030_split_b_v05:build_sequence",
        records=candidate.records,
        blocks=blocks,
        failures=candidate.failures,
        output_sha256=digest(array_path),
        sources={
            str(p.relative_to(ROOT)): digest(p)
            for p in (SOURCE_BANK, SOURCE_AUDIT, SOURCE_CONNECTION, args.mesh, Path(__file__))
        },
        formal_physical_validity_verdict=None,
    )
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("B_V05_PROBE_COMPLETE", len(candidate.failures), flush=True)


if __name__ == "__main__":
    main()
