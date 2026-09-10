# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Screen finite ST B IK branches against retained actual robot triangles [m]."""

import argparse
import hashlib
import itertools
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_branch_meshes import BranchMeshes, fcl
from op030_definition import ROOT
from op030_motion import SIDES
from op030_split_wire_motion import WirePlacementConfig, build_sequence, current_time, reference_time
from scipy.spatial.transform import Rotation
from solve_op030_motion import R, capture_robots


class SplitBMeshes(BranchMeshes):
    """Actual exported ST B triangles, including dynamic wire tubes [m]."""

    def __init__(self, sequence, path=None):
        self.sequence = sequence
        path = path or ROOT / "data/op030_split_b_meshes.npz"
        self.export = json.loads((ROOT / "audit" / (path.stem + ".json")).read_text())
        with np.load(path) as saved:
            data = {name: saved[name].copy() for name in saved.files}
        self.fixed_base = data["fixed_base"]
        names, nodes, actors = list(data["names"]), list(data["nodes"]), list(data["actors"])
        self.objects, centers, extents = [], [], []
        for index in range(len(names)):
            vertices = data["vertices"][data["vertex_offsets"][index] : data["vertex_offsets"][index + 1]]
            faces = data["faces"][data["face_offsets"][index] : data["face_offsets"][index + 1]]
            self.objects.append(self._object(vertices, faces))
            centers.append((vertices.min(0) + vertices.max(0)) / 2)
            extents.append((vertices.max(0) - vertices.min(0)) / 2)
        self.wire_indices, self.wire_cache = {}, {}
        initial = sequence.evaluate(0.0)
        for uid, record in initial["wires"].items():
            bend = sequence.bends[record["number"]]
            vertices, quads = bend.tube_mesh(record["shape"])
            faces = np.vstack((quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]))
            self.wire_indices[uid] = len(names)
            names.append(uid + "_insulation")
            actors.append(uid + "_insulation")
            nodes.append(-1)
            self.objects.append(self._object(vertices, faces))
            centers.append((vertices.min(0) + vertices.max(0)) / 2)
            extents.append((vertices.max(0) - vertices.min(0)) / 2)
        self.names, self.nodes, self.actors = np.asarray(names), np.asarray(nodes), np.asarray(actors)
        self.centers, self.extents = np.asarray(centers), np.asarray(extents)
        self.actor_indices = {name: np.flatnonzero(self.actors == name) for name in set(self.actors)}
        self.side = np.where(self.nodes < 0, -2, np.where(self.nodes < 1000, -1, np.where(self.nodes < 1084, 0, 1)))
        local = self.nodes - np.where(self.side == 0, 1046, 1086)
        links = np.searchsorted([3, 5, 10, 15, 18, 20, 21, 38], local, side="right")
        a, b = np.triu_indices(len(names), 1)
        nonadjacent = (
            (self.side[a] < 0) | (self.side[b] < 0) | (self.side[a] != self.side[b]) | (abs(links[a] - links[b]) > 1)
        )
        mount = ((self.nodes[a] == 578) & np.isin(self.nodes[b], [1046, 1086])) | (
            (self.nodes[b] == 578) & np.isin(self.nodes[a], [1046, 1086])
        )
        use = nonadjacent & ~mount
        # Internal crimp/sleeve overlaps and internal hinge joints are not an
        # external collision query. This exclusion does not assert their fit.
        for uid in initial["wires"]:
            inside = np.array([name.startswith(uid + "_") for name in names])
            use &= ~(inside[a] & inside[b])
        for number in (1, 2):
            inside = np.array([name.startswith(f"OP030B_check_transport_H{number}_") for name in names])
            use &= ~(inside[a] & inside[b])
        self.all_a, self.all_b = a[use], b[use]
        robot_relevant = use & ((self.side[a] >= 0) | (self.side[b] >= 0))
        self.a, self.b = a[robot_relevant], b[robot_relevant]
        self.pair_cache = {}
        self.world = np.repeat(np.eye(4)[None], len(names), axis=0)
        self.request = fcl.CollisionRequest(num_max_contacts=1, enable_contact=False)
        self.set_poses(dict(zip(data["actor_world_names"], data["actor_world"], strict=True)))
        self.current_holds = {}

    @staticmethod
    def _object(vertices, faces):
        mesh = fcl.BVHModel()
        mesh.beginModel(len(vertices), len(faces))
        mesh.addSubModel(np.asarray(vertices), np.asarray(faces))
        mesh.endModel()
        return fcl.CollisionObject(mesh, fcl.Transform())

    def set_state(self, target):
        """Apply all unchanged target identities and exact tube geometry [m]."""
        self.current_holds = target["holds"]
        self.set_poses({576: self.fixed_base, 577: target["root"], 578: target["root"]})
        for uid, record in target["wires"].items():
            shape = record["shape"]
            self.set_poses({uid + "_" + end: frame for end, frame in shape.lug_frames.items()})
            key = shape.centerline.tobytes()
            if self.wire_cache.get(uid) != key:
                self.wire_cache[uid] = key
                vertices, quads = self.sequence.bends[record["number"]].tube_mesh(shape)
                faces = np.vstack((quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]))
                index = self.wire_indices[uid]
                self.objects[index] = self._object(vertices, faces)
                self.centers[index] = (vertices.min(0) + vertices.max(0)) / 2
                self.extents[index] = (vertices.max(0) - vertices.min(0)) / 2
        for record in self.export["clip_actors"]:
            hinge, pads = target["clips"][record["number"]]
            geometry = next(
                item for item in self.export["clip_metadata"]["clips"] if item["number"] == record["number"]
            )
            swing = np.eye(4)
            swing[:3, 3] = np.asarray(record["swing_rest"])[:3, 3]
            angle = geometry["open_hinge_y_rad"] * (1 - hinge) + geometry["closed_hinge_y_rad"] * hinge
            swing[:3, :3] = Rotation.from_euler("y", angle).as_matrix()
            swing = np.asarray(record["fixed_world"]) @ swing
            matrices = {record["swing"]: swing}
            for sign, name in zip((-1, 1), record["pads"], strict=True):
                pad = np.eye(4)
                pad[0, 3] = sign * 0.011 * (1 - pads)
                matrices[name] = swing @ np.asarray(record["head_local"]) @ pad
            self.set_poses(matrices)

    def score(self, side, extra_actors=()):
        key = (side, tuple(extra_actors))
        if key not in self.pair_cache:
            a, b = (self.all_a, self.all_b) if extra_actors else (self.a, self.b)
            moving = np.isin(self.actors, extra_actors)
            active = (self.side[a] == side) | (self.side[b] == side) | moving[a] | moving[b]
            self.pair_cache[key] = a[active], b[active]
        a, b = self.pair_cache[key]
        rotation = self.world[:, :3, :3]
        xyz = np.einsum("nij,nj->ni", rotation, self.centers) + self.world[:, :3, 3]
        extent = np.einsum("nij,nj->ni", abs(rotation), self.extents)
        mask = np.all(extent[a] + extent[b] - abs(xyz[a] - xyz[b]) > 1e-5, axis=1)
        hits, interfaces = [], []
        for i, j in zip(a[mask], b[mask], strict=True):
            intended = False
            for tip, wire in ((i, j), (j, i)):
                arm = int(self.side[tip])
                hold = self.current_holds.get(arm)
                if (
                    hold
                    and "_precision_" in self.names[tip]
                    and self.names[tip].endswith("_tip")
                    and self.names[wire] == hold[0] + "_insulation"
                ):
                    intended = True
            if intended:
                interfaces.append((self.names[i], self.names[j]))
                continue
            result = fcl.CollisionResult()
            fcl.collide(self.objects[i], self.objects[j], self.request, result)
            if result.is_collision:
                hits.append((self.names[i], self.names[j]))
        self.last_pairs, self.last_grip_interfaces = hits, interfaces
        return float(10 * len(hits))


def unique_branches(section: dict, data: dict) -> list[dict]:
    """Return physically distinct endpoint branches, modulo joint turns [rad]."""
    selected = []
    for record in section["branches"]:
        if not record["feasible"]:
            continue
        candidate = data[record["array_key"]][0]
        if any(
            np.max(abs(np.arctan2(np.sin(candidate - old["joints"][0]), np.cos(candidate - old["joints"][0])))) < 0.01
            for old in selected
        ):
            continue
        selected.append({**record, "joints": data[record["array_key"]]})
    return selected


def screen_robot_branches(sequence=None, branch_prefix="op030_split_wire_motion_branches", native_times=False) -> dict:
    """Check self, mutual-arm, body and mounted-camera surfaces only."""
    sequence = sequence or build_sequence()
    with np.load(ROOT / "analysis" / (branch_prefix + ".npz")) as saved:
        data = {name: saved[name].copy() for name in saved.files}
    sections = json.loads((ROOT / "audit" / (branch_prefix + ".json")).read_text())["sections"]
    screen = BranchMeshes()
    # All negative nodes in the old export are environment and carried actors.
    # Neither old tooling nor old stock geometry belongs to this robot-only gate.
    active = (screen.nodes[screen.a] >= 0) & (screen.nodes[screen.b] >= 0)
    screen.a, screen.b = screen.a[active], screen.b[active]
    screen.pair_cache.clear()
    robots = capture_robots()
    reports = []
    for wire, left_index, right_index in ((2, 0, 2), (1, 1, 3)):
        left, right = sections[left_index], sections[right_index]
        candidates = [unique_branches(left, data), unique_branches(right, data)]
        times_left = data[f"section_{left_index}_times"]
        times_right = data[f"section_{right_index}_times"]
        times = np.unique(np.r_[times_left, times_right])
        times = times[(times >= max(times_left[0], times_right[0])) & (times <= min(times_left[-1], times_right[-1]))]
        targets = [
            sequence.evaluate(float(time) if native_times else current_time(sequence, float(time))) for time in times
        ]
        combinations = []
        for combination, (a, b) in enumerate(itertools.product(*candidates)):
            pair_counts, collisions = {}, []
            for index, (time, target) in enumerate(zip(times, targets, strict=True)):
                left_q = np.array([np.interp(time, times_left, a["joints"][:, joint]) for joint in range(6)])
                right_q = np.array([np.interp(time, times_right, b["joints"][:, joint]) for joint in range(6)])
                screen.set_poses({576: screen.fixed_base, 577: target["root"], 578: target["root"]})
                for arm, q in enumerate((left_q, right_q)):
                    robot, capture = robots[SIDES[arm]]
                    robot.base_pose = target["root"] @ R.yoke_base_pose(SIDES[arm])
                    robot.update(q, float(target["grips"][arm]))
                    screen.set_poses(capture.poses)
                screen.score(0)
                hits = list(screen.last_pairs)
                screen.score(1)
                hits = sorted(set(hits + screen.last_pairs))
                if hits:
                    collisions.append(
                        {
                            "time_s": float(time),
                            "phase_index": target["phase_index"],
                            "label": target["label"],
                            "pairs": hits,
                        }
                    )
                    for pair in hits:
                        key = " | ".join(pair)
                        pair_counts[key] = pair_counts.get(key, 0) + 1
            combinations.append(
                {
                    "left_branch": a["array_key"],
                    "right_branch": b["array_key"],
                    "sample_count": len(times),
                    "hit_sample_count": len(collisions),
                    "hits": collisions,
                    "pair_counts": pair_counts,
                    "screen_clear": not collisions,
                }
            )
            print("OP030B_ROBOT_BRANCH_FCL", wire, combination, len(collisions), flush=True)
        reports.append(
            {
                "wire": wire,
                "unique_left_branches": len(candidates[0]),
                "unique_right_branches": len(candidates[1]),
                "combinations": combinations,
                "clear_combination_count": sum(row["screen_clear"] for row in combinations),
            }
        )
    return {
        "observed_at": datetime.now().astimezone().isoformat(),
        "wires": reports,
        "all_wires_have_clear_robot_combination": all(row["clear_combination_count"] > 0 for row in reports),
        "scope": "Discrete actual-triangle robot self/mutual/body/onhand-camera screen only; "
        "no environment/wire geometry yet",
        "formal_physical_verdict": None,
        "inputs": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                ROOT / "data/op030_branch_meshes.npz",
                ROOT / "analysis" / (branch_prefix + ".npz"),
                ROOT / "scripts/op030_split_wire_motion.py",
                Path(__file__),
            )
        },
    }


def screen_held_environment(mesh_path=None, sequence=None, candidate_prefix=None, selected=None) -> dict:
    """Screen chosen held branches with supply, product, tubes and moving clips."""
    sequence = sequence or build_sequence()
    branch_prefix = candidate_prefix + "_branches" if candidate_prefix else "op030_split_wire_motion_branches"
    initial_prefix = candidate_prefix + "_reach" if candidate_prefix else "op030_split_wire_motion_initial"
    with np.load(ROOT / "analysis" / (branch_prefix + ".npz")) as saved:
        branches = {name: saved[name].copy() for name in saved.files}
    with np.load(ROOT / "analysis" / (initial_prefix + ".npz")) as saved:
        initial_times, initial_joints = saved["times"].copy(), saved["joints"].copy()
    selected = selected or {
        (2, 0): (0, "section_0_branch_2"),
        (2, 1): (2, "section_2_branch_0"),
        (1, 0): (1, "section_1_branch_2"),
        (1, 1): (3, "section_3_branch_0"),
    }
    screen = SplitBMeshes(sequence, mesh_path)
    robots = capture_robots()
    times = np.unique(
        np.r_[
            np.arange(0.0, sequence.time, 0.5),
            sequence.time,
            [phase["start"] for phase in sequence.phases],
            [phase["stop"] for phase in sequence.phases],
        ]
    )
    clip_times = []
    for phase in sequence.phases:
        if "仮保持クリップを旋回" in phase["label"]:
            angle = max(abs(item["open_hinge_y_rad"]) for item in screen.export["clip_metadata"]["clips"])
            count = int(np.ceil(np.degrees(angle))) + 1
            clip_times.extend(np.linspace(phase["start"], phase["stop"], count))
        elif "仮保持パッドを閉じる" in phase["label"]:
            clip_times.extend(np.linspace(phase["start"], phase["stop"], 23))
    times = np.unique(np.r_[times, clip_times])
    rows, pair_counts, checked = [], {}, 0
    for time in times:
        target = sequence.evaluate(float(time))
        if not target["holds"]:
            continue
        old_time = float(time) if candidate_prefix else reference_time(sequence, float(time))
        joints = np.array(
            [
                [np.interp(old_time, initial_times, initial_joints[:, arm, joint]) for joint in range(6)]
                for arm in (0, 1)
            ]
        )
        for arm, (uid, _) in target["holds"].items():
            number = target["wires"][uid]["number"]
            section, key = selected[number, arm]
            reference_times = branches[f"section_{section}_times"]
            joints[arm] = [np.interp(old_time, reference_times, branches[key][:, joint]) for joint in range(6)]
        screen.set_state(target)
        for arm, side in enumerate(SIDES):
            robot, capture = robots[side]
            robot.base_pose = target["root"] @ R.yoke_base_pose(side)
            robot.update(joints[arm], float(target["grips"][arm]))
            screen.set_poses(capture.poses)
        held_uids = {value[0] for value in target["holds"].values()}
        extra = [uid + suffix for uid in held_uids for suffix in ("_J1", "_T", "_insulation")]
        for record in screen.export["clip_actors"]:
            extra.extend([record["swing"], *record["pads"]])
        screen.score(0, tuple(sorted(extra)))
        hits = list(screen.last_pairs)
        screen.score(1)
        hits = sorted(set(hits + screen.last_pairs))
        if hits:
            rows.append({"time_s": float(time), "reference_time_s": old_time, "label": target["label"], "pairs": hits})
            for pair in hits:
                key = " | ".join(pair)
                pair_counts[key] = pair_counts.get(key, 0) + 1
        checked += 1
        if checked % 25 == 0:
            print("OP030B_HELD_ENVIRONMENT", checked, round(float(time), 3), len(rows), flush=True)
    return {
        "observed_at": datetime.now().astimezone().isoformat(),
        "sample_count": checked,
        "hit_sample_count": len(rows),
        "hits": rows,
        "pair_counts": pair_counts,
        "screen_clear": not rows,
        "selected_branches": {f"H{number}_{SIDES[arm]}": key for (number, arm), (_, key) in selected.items()},
        "scope": "Discrete actual mesh screen over held states; free-hand full-cycle paths not connected yet",
        "intentional_interfaces": "Each held wire versus that arm's precision finger tips excluded; "
        "rigid crimp internals and internal clip joints excluded",
        "formal_physical_verdict": None,
        "mesh_export_sha256": screen.export["output_sha256"],
        "clip_sweep_max_nominal_angle_step_deg": 1.0,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def main() -> None:
    """Write robot-only branch collisions without promoting failed paths."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="op030_split_b_robot_branches")
    parser.add_argument("--environment", action="store_true")
    parser.add_argument("--mesh", type=Path)
    parser.add_argument("--candidate_prefix")
    args = parser.parse_args()
    if args.candidate_prefix:
        reach = json.loads((ROOT / "audit" / (args.candidate_prefix + "_reach.json")).read_text())
        sequence = build_sequence(WirePlacementConfig(**reach["config"]))
        if args.environment:
            robot_report = json.loads((ROOT / "audit" / (args.candidate_prefix + "_robot.json")).read_text())
            selected = {}
            for entry in robot_report["wires"]:
                wire = entry["wire"]
                choice = next(item for item in entry["combinations"] if item["screen_clear"])
                for arm, key in enumerate(("left_branch", "right_branch")):
                    selected[wire, arm] = (int(choice[key].split("_")[1]), choice[key])
            result = screen_held_environment(args.mesh, sequence, args.candidate_prefix, selected)
        else:
            result = screen_robot_branches(sequence, args.candidate_prefix + "_branches", True)
    else:
        result = screen_held_environment(args.mesh) if args.environment else screen_robot_branches()
    (ROOT / "audit" / (args.output + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if args.environment:
        print("OP030B_HELD_ENVIRONMENT_COMPLETE", result["screen_clear"], flush=True)
    else:
        print("OP030B_ROBOT_BRANCH_FCL_COMPLETE", result["all_wires_have_clear_robot_combination"], flush=True)


if __name__ == "__main__":
    main()
