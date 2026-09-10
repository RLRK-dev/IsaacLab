# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Connect the finite ST B held branches using retained FK and OMPL [rad, s].

This module generates an auxiliary motion candidate, not a physical verdict.
The only support-contact exclusions are the four named, measured U interfaces
while their wire remains at the exact supply pose. Free paths use the existing
OMPL checker and stopped quintic timing implementation without changes.
"""

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import LIMITS, chain_for
from op030_motion import SIDES
from op030_split_b_check import SplitBMeshes
from op030_split_wire_motion import WirePlacementConfig, build_sequence, target_checks
from solve_op030_motion import R, capture_robots


def digest(path: Path) -> str:
    """Return the SHA256 of one unchanged input artifact."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Planner:
    """Finite branch connection and exact-pose triangle screening [m, rad, s]."""

    def __init__(self, prefix: str, mesh: Path, config_override: dict | None = None):
        self.prefix = prefix
        self.mesh = mesh.resolve()
        self.reach_path = ROOT / "audit" / (prefix + "_reach.json")
        reach = json.loads(self.reach_path.read_text())
        self.sequence = build_sequence(WirePlacementConfig(**(reach["config"] | (config_override or {}))))
        self.branch_path = ROOT / "analysis" / (prefix + "_branches.npz")
        with np.load(self.branch_path) as saved:
            self.branches = {key: saved[key].copy() for key in saved.files}
        with np.load(ROOT / "analysis" / (prefix + "_reach.npz")) as saved:
            self.initial_t, self.initial_q = saved["times"].copy(), saved["joints"].copy()
        robot_report = json.loads((ROOT / "audit" / (prefix + "_robot.json")).read_text())
        self.selected = {}
        for row in robot_report["wires"]:
            clear = next(item for item in row["combinations"] if item["screen_clear"])
            for arm, side in enumerate(SIDES):
                key = clear[side + "_branch"]
                self.selected[row["wire"], arm] = key
        self.screen = SplitBMeshes(self.sequence, self.mesh)
        self.robots = capture_robots()
        self.free_paths = {}
        self.failures = []
        self.support_contacts = []
        self.start_state = self.sequence.evaluate(0.0)
        self.blocks = []

    def solve(self, time: float, arm: int, seed: np.ndarray) -> tuple[np.ndarray, float]:
        """Use the retained analytic-Jacobian continuous IK at author time [s]."""
        target = self.sequence.evaluate(time)
        chain = chain_for(tuple((target["root"] @ R.yoke_base_pose(SIDES[arm])).ravel()))
        return chain.solve_continuous(target["tools"][arm], seed)

    def constraints(self, step: float = 0.1) -> dict:
        """Connect each constrained interval to its selected held branch [s]."""
        sequence = self.sequence
        self.times = np.unique(
            np.r_[
                np.arange(0.0, sequence.time, step),
                sequence.time,
                [p["start"] for p in sequence.phases],
                [p["stop"] for p in sequence.phases],
            ]
        )
        self.q = np.full((len(self.times), 2, 6), np.nan)
        self.maximum_residual = 0.0
        for arm in (0, 1):
            groups, current = [], []
            for i, phase in enumerate(sequence.phases):
                if phase["free_hands"][arm]:
                    if current:
                        groups.append(current)
                        current = []
                else:
                    current.append(i)
            if current:
                groups.append(current)
            for phases in groups:
                start, stop = sequence.phases[phases[0]]["start"], sequence.phases[phases[-1]]["stop"]
                indices = np.flatnonzero((self.times >= start - 1e-8) & (self.times <= stop + 1e-8))
                held = [i for i in indices if arm in sequence.evaluate(float(self.times[i]))["holds"]]
                if held:
                    anchor = held[len(held) // 2]
                    target = sequence.evaluate(float(self.times[anchor]))
                    uid = target["holds"][arm][0]
                    key = self.selected[target["wires"][uid]["number"], arm]
                    old_t = self.branches["_".join(key.split("_")[:2]) + "_times"]
                    seed = np.array([np.interp(self.times[anchor], old_t, self.branches[key][:, j]) for j in range(6)])
                else:
                    anchor = indices[0]
                    # Reuse the nearest preceding constrained branch as a seed;
                    # free transits may change IK branch only through a planned path.
                    previous = np.flatnonzero(np.isfinite(self.q[:anchor, arm, 0]))
                    seed = self.q[previous[-1], arm] if len(previous) else self.initial_q[0, arm]
                    label = sequence.phases[phases[0]]["label"]
                    if sequence.config.connection_mode == "top_entry" and (
                        "次の直線ケーブル供給へ旋回" in label or "内部配線2本の設置完了" in label
                    ):
                        # These unchanged empty-hand targets already have a
                        # retained supply-side park seed. Re-solve and screen
                        # it against the new geometry, never copy a verdict.
                        seed = self.initial_q[0, arm]
                solved, residual = self.solve(float(self.times[anchor]), arm, seed)
                self.q[anchor, arm] = solved
                samples = [int(anchor)]
                for direction in (-1, 1):
                    subset = indices[indices < anchor][::-1] if direction < 0 else indices[indices > anchor]
                    seed = solved.copy()
                    for index in subset:
                        q, error = self.solve(float(self.times[index]), arm, seed)
                        delta = float(np.max(abs(q - seed)))
                        residual = max(residual, error)
                        if error > 1e-5 or delta > 0.8:
                            self.failures.append(
                                {
                                    "kind": "constrained_ik",
                                    "time_s": float(self.times[index]),
                                    "arm": SIDES[arm],
                                    "residual": error,
                                    "delta_rad": delta,
                                }
                            )
                            break
                        self.q[index, arm] = q
                        seed = q
                        samples.append(int(index))
                # Equivalent whole-block turns avoid artificial limit crossings.
                for joint in range(6):
                    values = self.q[indices, arm, joint]
                    if not np.all(np.isfinite(values)):
                        continue
                    turns = [2 * np.pi * k for k in range(-2, 3) if np.max(abs(values + 2 * np.pi * k)) < LIMITS[joint]]
                    if not turns:
                        self.failures.append(
                            {
                                "kind": "joint_bounds",
                                "arm": SIDES[arm],
                                "start": start,
                                "stop": stop,
                                "joint": joint,
                                "range_rad": [float(values.min()), float(values.max())],
                            }
                        )
                    else:
                        shift = min(turns, key=lambda x: np.max(abs(values + x)))
                        self.q[indices, arm, joint] += shift
                self.maximum_residual = max(self.maximum_residual, float(residual))
                self.blocks.append(
                    {
                        "arm": arm,
                        "start": start,
                        "stop": stop,
                        "phases": phases,
                        "anchor_time": float(self.times[anchor]),
                        "maximum_residual": float(residual),
                    }
                )
                print("OP030B_CONSTRAINED_BLOCK", SIDES[arm], start, stop, residual, len(self.failures), flush=True)
        # Consecutive free phases (retreat then park) share an authored
        # intermediate endpoint but have no constrained block between them.
        # Resolve each such endpoint once, and retain it for both adjacent paths.
        for time in sorted({p[key] for p in sequence.phases for key in ("start", "stop")}):
            index = int(np.flatnonzero(abs(self.times - time) < 1e-8)[0])
            for arm in (0, 1):
                if np.all(np.isfinite(self.q[index, arm])):
                    continue
                previous = np.flatnonzero(np.isfinite(self.q[:index, arm, 0]))
                seed = self.q[previous[-1], arm] if len(previous) else self.initial_q[0, arm]
                q, error = self.solve(time, arm, seed)
                if error > 1e-5 or np.any(abs(q) >= LIMITS):
                    self.failures.append(
                        {"kind": "consecutive_free_endpoint", "time_s": time, "arm": SIDES[arm], "residual": error}
                    )
                self.q[index, arm] = q
        return {"blocks": self.blocks, "failures": self.failures, "maximum_residual": self.maximum_residual}

    def at(self, time: float) -> np.ndarray:
        """Interpolate only already-solved constrained joint samples [rad]."""
        return np.array([[np.interp(time, self.times, self.q[:, arm, joint]) for joint in range(6)] for arm in (0, 1)])

    def repair_park_branches(self, previous: str) -> dict:
        """Reuse solved intervals and use the verified initial park branch [rad]."""
        path = ROOT / "analysis" / (previous + ".npz")
        report = json.loads((ROOT / "audit" / (previous + ".json")).read_text())
        if digest(path) != report["npz_sha256"]:
            raise ValueError("Previous connection changed")
        with np.load(path) as saved:
            self.times, self.q = saved["times"].copy(), saved["joints"].copy()
            for key in saved.files:
                if key.startswith("free_") and key.endswith("_points"):
                    _, phase, order, _ = key.split("_")
                    stem = f"free_{phase}_{order}_"
                    self.free_paths.setdefault(int(phase), []).append(
                        {
                            "order": int(order),
                            "arm": int(saved[stem + "arm"]),
                            "points": saved[key].copy(),
                            "fixed": saved[stem + "fixed"].copy(),
                        }
                    )
        for paths in self.free_paths.values():
            paths.sort(key=lambda item: item["order"])
        self.blocks = report["constraints"]["blocks"]
        self.maximum_residual = report["constraints"]["maximum_residual"]
        changed = []
        for block in self.blocks:
            label = self.sequence.phases[block["phases"][0]]["label"]
            if "次の直線ケーブル供給へ旋回" not in label and "内部配線2本の設置完了" not in label:
                continue
            arm = block["arm"]
            indices = np.flatnonzero((self.times >= block["start"] - 1e-8) & (self.times <= block["stop"] + 1e-8))
            seed = self.q[0, arm].copy()
            for index in indices:
                q, error = self.solve(float(self.times[index]), arm, seed)
                if error > 1e-5 or np.any(abs(q) >= LIMITS):
                    self.failures.append(
                        {
                            "kind": "park_branch_repair",
                            "time_s": float(self.times[index]),
                            "arm": arm,
                            "residual": error,
                        }
                    )
                self.q[index, arm] = q
                seed = q
            changed.append({"arm": arm, "start": block["start"], "stop": block["stop"], "label": label})
        if self.sequence.config.h1_release_gap is not None:
            phase = next(p for p in self.sequence.phases if p["label"] == "H03-1／右指を開く")
            retreat = next(p for p in self.sequence.phases if p["label"] == "H03-1／右指を外側上方へ退避")
            indices = np.flatnonzero(
                ((self.times >= phase["start"] - 1e-8) & (self.times <= phase["stop"] + 1e-8))
                | (abs(self.times - retreat["stop"]) < 1e-8)
            )
            for index in indices:
                q, error = self.solve(float(self.times[index]), 1, self.q[index, 1])
                if error > 1e-5 or np.any(abs(q) >= LIMITS):
                    self.failures.append(
                        {"kind": "staged_release_ik", "time_s": float(self.times[index]), "residual": error}
                    )
                self.q[index, 1] = q
            changed.append(
                {
                    "arm": 1,
                    "start": phase["start"],
                    "stop": retreat["stop"],
                    "label": "H1 staged 20 mm release and retreat endpoints; holds unchanged",
                }
            )
        return {
            "blocks": self.blocks,
            "maximum_residual": self.maximum_residual,
            "reused_npz_sha256": digest(path),
            "changed_park_blocks": changed,
            "failures": self.failures,
        }

    def score(self, target: dict, joints: np.ndarray, extra_wires: bool = True) -> tuple[float, list]:
        """Return actual-mesh hits with only named exact-rest support contacts split out."""
        screen = self.screen
        screen.set_state(target)
        for arm, side in enumerate(SIDES):
            robot, capture = self.robots[side]
            robot.base_pose = target["root"] @ R.yoke_base_pose(side)
            robot.update(joints[arm], float(target["grips"][arm]))
            screen.set_poses(capture.poses)
        extra = []
        if extra_wires:
            for uid in set(item[0] for item in target["holds"].values()):
                extra.extend(uid + suffix for suffix in ("_J1", "_T", "_insulation"))
        for clip in screen.export["clip_actors"]:
            extra.extend([clip["swing"], *clip["pads"]])
        screen.score(0, tuple(sorted(extra)))
        hits = list(screen.last_pairs)
        screen.score(1)
        hits = sorted(set(hits + screen.last_pairs))
        allowed = set()
        for row in self.sequence.rows:
            uid = row["uid"]
            points = target["wires"][uid]["shape"].centerline
            if (
                uid in self.sequence.active_uids.values()
                and np.max(abs(points - self.start_state["wires"][uid]["shape"].centerline)) < 1e-10
            ):
                row_index = next(i for i, old in enumerate(self.sequence.rows) if old["uid"] == uid)
                allowed.update(
                    frozenset((f"OP030B_wire_supply_row{row_index:02d}_saddle{k}", uid + "_insulation")) for k in (0, 1)
                )
        actual = []
        for pair in hits:
            if frozenset(pair) in allowed:
                self.support_contacts.append({"time_s": target["time"], "pair": pair})
            else:
                actual.append(pair)
        return 10.0 * len(actual), actual

    def free(self) -> dict:
        """Plan each free-hand interval in two finite arm orders [rad, s]."""
        from op030_free_paths import plan_free_path

        records = []
        for index, phase in enumerate(self.sequence.phases):
            arms = np.flatnonzero(phase["free_hands"]).tolist()
            if not arms:
                continue
            if index in self.free_paths:
                records.append({"phase_index": index, "label": phase["label"], "found": True, "reused": True})
                continue
            q0, q1 = self.at(phase["start"]), self.at(phase["stop"])
            # At a free endpoint the opposite arm can be in the interior of its
            # continuous constrained interval; refine both endpoint targets.
            for endpoint, q in ((phase["start"], q0), (phase["stop"], q1)):
                for arm in (0, 1):
                    if not np.all(np.isfinite(q[arm])):
                        raise ValueError(f"Missing constrained endpoint {index} {endpoint} {arm}")
                    q[arm], error = self.solve(endpoint, arm, q[arm])
                    if error > 1e-5:
                        raise ValueError(f"Endpoint IK failed {index} {endpoint} {arm}: {error}")
            candidates = [arms, arms[::-1]] if len(arms) == 2 else [arms]
            attempts = []
            for order in candidates:
                current = q0.copy()
                paths = []
                target = self.sequence.evaluate(phase["stop"] - 1e-8)
                for arm in order:
                    static_score, static_pairs = self.score(target, current)
                    # Root, clips, wires and the other arm are fixed in this leg.
                    # Check that state once, then query all pairs of the moving arm.
                    robot, capture = self.robots[SIDES[arm]]

                    def cost(q, arm=arm, robot=robot, capture=capture):
                        robot.update(q, float(target["grips"][arm]))
                        self.screen.set_poses(capture.poses)
                        return self.screen.score(arm)

                    if static_score > 0:
                        attempts.append(
                            {
                                "order": order,
                                "arm": arm,
                                "found": False,
                                "reason": "fixed start state",
                                "start_pairs": static_pairs,
                            }
                        )
                        break

                    planned = plan_free_path(current[arm], q1[arm], cost)
                    attempts.append(
                        {"order": order, "arm": arm, **plan_free_path.last_debug, "found": planned is not None}
                    )
                    if planned is None:
                        _, pairs = self.score(target, current)
                        attempts[-1]["start_pairs"] = pairs
                        endpoint = current.copy()
                        endpoint[arm] = q1[arm]
                        attempts[-1]["stop_pairs"] = self.score(target, endpoint)[1]
                        break
                    paths.append({"arm": arm, "points": planned, "fixed": current.copy()})
                    current[arm] = q1[arm]
                else:
                    self.free_paths[index] = paths
                    break
            record = {
                "phase_index": index,
                "label": phase["label"],
                "attempts": attempts,
                "found": index in self.free_paths,
            }
            records.append(record)
            print("OP030B_FREE_CONNECTION", index, phase["label"], record["found"], flush=True)
            if not record["found"]:
                self.failures.append({"kind": "free_path", **record})
                break
        return {"records": records, "failures": self.failures}


def main() -> None:
    """Generate one named, non-overwriting bounded connection candidate."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="op030_split_wire_h1delta")
    parser.add_argument("--output", default="op030_split_b_h1delta_connection")
    parser.add_argument("--mesh", type=Path, default=ROOT / "data/op030_split_b_meshes_angle90.npz")
    parser.add_argument("--constraints_only", action="store_true")
    parser.add_argument("--reuse_park_fix")
    parser.add_argument("--h1_release_gap", type=float)
    parser.add_argument("--connection_mode", choices=("rear_entry", "top_entry"))
    args = parser.parse_args()
    path = ROOT / "audit" / (args.output + ".json")
    if path.exists():
        raise FileExistsError(path)
    override = {} if args.h1_release_gap is None else {"h1_release_gap": args.h1_release_gap}
    if args.connection_mode is not None:
        override["connection_mode"] = args.connection_mode
    planner = Planner(args.prefix, args.mesh, override)
    report = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "config": asdict(planner.sequence.config),
        "mesh": str(planner.mesh.resolve().relative_to(ROOT)),
        "prefix": planner.prefix,
        "clip_open_hinge_degrees": 90.0,
        "target_checks": target_checks(planner.sequence),
        "constraints": planner.repair_park_branches(args.reuse_park_fix)
        if args.reuse_park_fix
        else planner.constraints(),
        "formal_physical_verdict": None,
    }
    if not planner.failures and not args.constraints_only:
        report["free"] = planner.free()
    report["support_contacts"] = planner.support_contacts
    report["failures"] = planner.failures
    report["sources"] = {
        str(p.relative_to(ROOT)): digest(p)
        for p in (
            Path(__file__),
            ROOT / "scripts/op030_split_wire_motion.py",
            ROOT / "scripts/op030_split_wire.py",
            ROOT / "scripts/op030_split_b_check.py",
            planner.branch_path,
            planner.mesh,
        )
    }
    arrays = {"times": planner.times, "joints": planner.q}
    for index, paths in planner.free_paths.items():
        for order, record in enumerate(paths):
            arrays[f"free_{index}_{order}_points"] = record["points"]
            arrays[f"free_{index}_{order}_fixed"] = record["fixed"]
            arrays[f"free_{index}_{order}_arm"] = np.array(record["arm"])
    npz = ROOT / "analysis" / (args.output + ".npz")
    np.savez_compressed(npz, **arrays)
    report["npz_sha256"] = digest(npz)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("OP030B_CONNECTION_COMPLETE", not planner.failures, flush=True)


if __name__ == "__main__":
    main()
