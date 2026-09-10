# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse C native meshes and measured seating for concurrent v05 candidates [m, rad, s]."""

import argparse
import json
from copy import copy
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT, pose
from op030_split_ac_meshes import BranchMeshes
from op030_split_c_v04 import digest, load
from scipy.spatial.transform import Rotation
from solve_op030_motion import NODE_IDS, R, capture_robots
from split_tools_audit_a_bank_mesh_v04 import OutsideSupportCheck
from split_tools_c_top_entry_plan import PlanningContext as ContactCalibration

MESH = ROOT / "data/op030_split_c_fixed_installation_v04_meshes.npz"


class Context:
    """Apply both actual FK arms and carried UIDs at one shared clock [m, rad, s]."""

    def __init__(self, names: np.ndarray, mesh_file: Path = MESH):
        self.mesh_file = mesh_file
        self.metadata = json.loads(mesh_file.with_suffix(".json").read_text())
        data = load(mesh_file)
        self.screen = BranchMeshes(mesh_file)
        if any("OP030_transport_H" in str(name) for name in self.screen.names):
            raise ValueError("Removed transport clips in C export")
        self.names = names
        self.extra = tuple(str(name) for name in names if "feeder" in str(name))
        if any(self.screen._name(name) not in self.screen.actor_world for name in self.extra):
            raise ValueError("A finite feeder/gate actor is missing from the native export")
        self.contacts = ContactCalibration.__new__(ContactCalibration)
        self.contacts.screen, self.contacts.contact_records, self.contacts.seating = self.screen, {}, []
        for number, used in ((2, 1), (1, 2)):
            wire = "OP030B_H03_2_UID001" if number == 2 else "OP030B_H03_1_UID005"
            for end, size, part, thickness in (("J1", "M6", "6R6", 0.0038), ("T", "M14", "6R14", 0.0032)):
                lug = f"{wire}_{end}_{part}"
                washer = f"OP030C_feeder_{size}_UID{used:03d}_washer"
                index = int(np.flatnonzero(self.screen.names == lug)[0])
                vertices = data["vertices"][data["vertex_offsets"][index] : data["vertex_offsets"][index + 1]]
                self.contacts.seating.append(
                    (
                        lug,
                        washer,
                        index,
                        vertices,
                        thickness,
                        0.0033 if size == "M6" else 0.0073,
                        0.006 if size == "M6" else 0.014,
                    )
                )
        self.active_contacts = ()
        self.robots = capture_robots()
        self.outside_path = ROOT / "data/op030_duct_support_v04_world_02.npz"
        self.background_path = ROOT / "data/op030_downstream_restored_v04_world.npz"
        # Outside exports use global coordinates; C is evaluated in its baseline frame.
        self.outside = OutsideSupportCheck(self.outside_path, self.screen, names)
        full = copy(self.screen)
        full.names = np.asarray([], dtype=str)
        self.background = OutsideSupportCheck(self.background_path, full, names)
        with np.load(self.background_path) as restored:
            replaced = np.isin(self.screen.names, restored["names"])
        self.replaced_background_names = self.screen.names[replaced].tolist()
        first, second = self.screen.all_a, self.screen.all_b
        keep = ~replaced[first] & ~replaced[second]
        self.screen.all_a, self.screen.all_b = first[keep], second[keep]
        self.screen.pair_cache.clear()
        for checker in (self.outside, self.background):
            checker.centers[:, 1] -= 4.6
            for obj in checker.objects:
                from op030_split_ac_meshes import fcl

                obj.setTransform(fcl.Transform(np.eye(3), np.array([0.0, -4.6, 0.0])))

    def query(self, row: dict, joints: np.ndarray | None = None) -> tuple[list, dict]:
        """Check exact native geometry, rebasing held UIDs if q changes [m, rad]."""
        joints = row["joints"] if joints is None else joints
        root = row["poses"][0]
        values = dict(zip(self.names, row["object_poses"], strict=True))
        values = {name: matrix.copy() for name, matrix in values.items()}
        captures, tools, residuals = {577: root, 578: root}, [], []
        self.screen.set_poses({577: root, 578: root})
        for arm, side in enumerate(("left", "right")):
            robot, capture = self.robots[side]
            robot.base_pose = root @ R.yoke_base_pose(side)
            actual = robot.update(joints[arm], 0.0)
            captures.update(capture.poses)
            self.screen.set_poses(capture.poses)
            size = "M6" if arm == 0 else "M14"
            record = self.metadata["fixed_tools"]["OP030C_" + size]
            tcp = actual @ np.asarray(record["flange_to_tcp"])
            driver = "OP030C_driver_" + size
            previous = values[driver].copy()
            values[driver] = tcp
            for uid, owner in zip(row["ledger_uids"], row["ledger_owner"], strict=True):
                if int(owner) == arm + 1:
                    values[str(uid)] = tcp @ np.linalg.inv(previous) @ values[str(uid)]
            spindle = tcp @ np.asarray(record["spindle_relative_to_tcp"])
            spindle = spindle @ pose(Rotation.from_euler("z", row["spindle_angles"][arm]).as_matrix())
            self.screen.set_poses({record["spindle"]: spindle})
            tools.append(actual.copy())
            residuals.append(float(abs(actual - row["tools"][arm]).max()))
        self.screen.set_poses(values)
        contacts = tuple(self.contacts.seating_contacts())
        if contacts != self.active_contacts:
            self.screen.set_contact_pairs(contacts)
            self.active_contacts = contacts
        self.screen.score(None, extra_actors=self.extra)
        hits = list(self.screen.last_pairs)
        hits += self.outside.query(self.screen)
        hits += self.background.query(self.screen)
        return hits, dict(
            poses=np.asarray([captures[int(node)] for node in NODE_IDS]),
            tools=np.asarray(tools),
            object_poses=np.asarray([values[name] for name in self.names]),
            maximum_original_tool_delta=float(max(residuals)),
        )


def bank_row(data: dict, index: int) -> dict:
    """Read one pose/ownership state from a stored bank [m, rad]."""
    result = {
        key: data[key][index] for key in ("joints", "poses", "tools", "object_poses", "spindle_angles", "ledger_owner")
    }
    result["ledger_uids"] = data["ledger_uids"]
    return result


def check(bank: Path, output: Path, mesh_file: Path = MESH, stride: int = 1) -> None:
    """Read and inspect selected actual native frames without changing the bank [s]."""
    if output.exists():
        raise FileExistsError(output)
    data = load(bank)
    context = Context(data["object_names"], mesh_file)
    inputs = [
        bank,
        mesh_file,
        mesh_file.with_suffix(".json"),
        context.outside_path,
        context.background_path,
        Path(__file__),
        ROOT / "scripts/op030_split_ac_meshes.py",
    ]
    hashes = {str(path): digest(path) for path in inputs}
    hits, failures, maximum = [], [], 0.0
    indices = np.unique(np.r_[np.arange(0, len(data["times"]), stride), len(data["times"]) - 1])
    for index in indices:
        pairs, actual = context.query(bank_row(data, index))
        maximum = max(maximum, actual["maximum_original_tool_delta"])
        if actual["maximum_original_tool_delta"] > 1e-6:
            failures.append(dict(frame=int(index + 1), maximum_matrix_error=actual["maximum_original_tool_delta"]))
        if pairs:
            hits.append(
                dict(
                    frame=int(index + 1),
                    time_s=float(data["times"][index]),
                    label=str(data["labels"][index]),
                    pairs=pairs,
                )
            )
        if index % 300 == 0:
            print("C_V05_NATIVE", index, len(data["times"]), len(hits), flush=True)
    unchanged = hashes == {str(path): digest(path) for path in inputs}
    result = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        bank=str(bank),
        bank_sha256=digest(bank),
        source_inputs_sha256=hashes,
        inputs_unchanged=unchanged,
        frames=len(data["times"]),
        checked_frames=len(indices),
        stride=stride,
        maximum_actual_fk_matrix_error=maximum,
        fk_failures=failures,
        collision_frames=hits,
        collision_frame_count=len(hits),
        measured_seating_contacts=context.contacts.contact_records,
        dynamic_extra_actors=list(context.extra),
        replaced_background_names=context.replaced_background_names,
        outside_support_aabb_separation_m=context.outside.minimum_aabb_separation_m,
        restored_background_aabb_separation_m=context.background.minimum_aabb_separation_m,
        passed=not hits and not failures and unchanged,
        additional_contact_exceptions=[],
        scope="Concurrent actual FK/meshes/all 24 fastener UIDs/gates; no force or formal physical verdict",
    )
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("C_V05_NATIVE_COMPLETE", len(indices), len(hits), len(failures), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mesh_file", type=Path, default=MESH)
    parser.add_argument("--stride", type=int, default=1)
    args = parser.parse_args()
    check(args.bank, args.output, args.mesh_file, args.stride)


if __name__ == "__main__":
    main()
