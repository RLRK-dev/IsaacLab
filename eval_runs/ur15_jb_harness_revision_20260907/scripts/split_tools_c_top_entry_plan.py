# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Screen top-entry C branches with both fixed tools and exact exported meshes."""

import hashlib
import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
from op030_contacts import TOLERANCE
from op030_definition import ROOT, pose
from op030_motion import SIDES
from op030_split_a_plan import compatibility, screen_branches
from op030_split_ac_meshes import BranchMeshes
from op030_split_top_entry_motion import top_entry_c_sequence
from scipy.spatial.transform import Rotation
from solve_op030_motion import R, capture_robots


class PlanningContext:
    """Use actual original FK poses and explicit variant calibration [m]."""

    def __init__(self, mesh_file: str | Path):
        self.mesh_file = Path(mesh_file)
        self.sequence = top_entry_c_sequence(self.mesh_file)
        self.screen = BranchMeshes(self.mesh_file)
        self.robots = capture_robots()
        self.driver_records = json.loads(self.mesh_file.with_suffix(".json").read_text())["fixed_tools"]
        self.contact_records = {}
        self.active_contact_pairs = ()
        self.seating = []
        with np.load(self.mesh_file) as saved:
            for number, used in ((2, 1), (1, 2)):
                wire = "OP030B_H03_2_UID001" if number == 2 else "OP030B_H03_1_UID005"
                for end, size, part, thickness in (("J1", "M6", "6R6", 0.0038), ("T", "M14", "6R14", 0.0032)):
                    lug_name = f"{wire}_{end}_{part}"
                    washer_name = f"OP030C_feeder_{size}_UID{used:03d}_washer"
                    index = int(np.flatnonzero(self.screen.names == lug_name)[0])
                    vertices = saved["vertices"][
                        saved["vertex_offsets"][index] : saved["vertex_offsets"][index + 1]
                    ].copy()
                    self.seating.append(
                        (
                            lug_name,
                            washer_name,
                            index,
                            vertices,
                            thickness,
                            0.0033 if size == "M6" else 0.0073,
                            0.006 if size == "M6" else 0.014,
                        )
                    )

    def seating_contacts(self):
        """Reuse the original measured washer/CAD-face contact rule [m]."""
        pairs = []
        for lug_name, washer_name, index, vertices, thickness, inner, outer in self.seating:
            washer_index = int(np.flatnonzero(self.screen.names == washer_name)[0])
            lug_world = self.screen.world[index]
            nut_world = self.screen.world[washer_index]
            relative = np.linalg.inv(lug_world) @ nut_world
            lateral = float(np.linalg.norm(relative[:2, 3]))
            axial = float(relative[2, 3] - thickness)
            normal = float(np.linalg.norm(relative[:3, 2] - [0, 0, 1]))
            if lateral > TOLERANCE or abs(axial) > TOLERANCE or normal > 1e-4:
                continue
            transform = np.linalg.inv(nut_world) @ lug_world
            points = vertices @ transform[:3, :3].T + transform[:3, 3]
            radius = np.linalg.norm(points[:, :2], axis=1)
            inside = (radius >= inner - TOLERANCE) & (radius <= outer + TOLERANCE)
            protrusion = float(points[inside, 2].max()) if inside.any() else float("inf")
            if protrusion <= TOLERANCE:
                pairs.append((lug_name, washer_name))
                self.contact_records[washer_name] = dict(
                    lug=lug_name,
                    washer=washer_name,
                    lateral_error_m=lateral,
                    axial_seating_error_m=axial,
                    normal_error=normal,
                    maximum_lug_protrusion_m=protrusion,
                    tolerance_m=TOLERANCE,
                )
        return pairs

    @lru_cache(maxsize=512)
    def state(self, time: float):
        phase = next((p for p in self.sequence.phases if time <= p["stop"] + 1e-8), self.sequence.phases[-1])
        return self.sequence.evaluate(time), phase, (), tuple(phase["before"]["driven_nuts"])

    def query(self, time, joints, *, side=None, hide_other=False, override_free=False):
        target, phase, grasp, extra = self.state(time)
        if hide_other:
            driver = self.sequence.driver_names[side]
            extra = tuple(uid for uid in extra if phase["before"]["driven_nuts"][uid][0] == driver)
        self.screen.set_poses(target["objects"])
        self.screen.set_poses({577: target["root"], 578: target["root"]})
        for arm, name in enumerate(SIDES):
            robot, capture = self.robots[name]
            robot.base_pose = target["root"] @ R.yoke_base_pose(name)
            actual = robot.update(joints[arm], 0.0)
            poses = capture.poses
            record = self.driver_records["OP030C_" + self.sequence.driver_sizes[arm]]
            tcp = actual @ np.asarray(record["flange_to_tcp"])
            spindle = (
                tcp
                @ np.asarray(record["spindle_relative_to_tcp"])
                @ pose(Rotation.from_euler("z", target["spindle_angles"][arm]).as_matrix())
            )
            if hide_other and arm != side:
                poses = {key: value.copy() for key, value in poses.items()}
                for value in poses.values():
                    value[2, 3] += 100
                spindle[2, 3] += 100
            self.screen.set_poses(poses)
            self.screen.set_poses({record["spindle"]: spindle})
            if override_free and target["free"][arm]:
                goal = target["tools"][arm]
                for uid, (driver, _) in phase["before"]["driven_nuts"].items():
                    if self.sequence.driver_names[arm] == driver:
                        self.screen.set_poses({uid: actual @ np.linalg.inv(goal) @ target["objects"][uid]})
        contact_pairs = tuple(self.seating_contacts())
        if contact_pairs != self.active_contact_pairs:
            self.screen.set_contact_pairs(contact_pairs)
            self.active_contact_pairs = contact_pairs
        score = self.screen.score(side, extra_actors=extra, grasp_actors=grasp)
        return score, list(self.screen.last_pairs)


def main():
    path = ROOT / "data/op030_split_c_top_entry_meshes.npz"
    context = PlanningContext(path)
    report = json.loads((ROOT / "audit/split_tools_c_top_entry_yaw110_branches.json").read_text())
    with np.load(ROOT / "analysis/split_tools_c_top_entry_yaw110_branches.npz") as saved:
        data = {key: saved[key].copy() for key in saved.files}
    sections = screen_branches(context, report, data)
    pairs = compatibility(context, sections, data) if all(row["clear_count"] for row in sections) else []
    result = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        mesh_file=str(path),
        mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        sections=sections,
        compatibility=pairs,
        all_sections_have_individually_clear_branch=all(row["clear_count"] for row in sections),
        factory="op030_split_top_entry_motion:top_entry_c_sequence",
        measured_seating_contacts=list(context.contact_records.values()),
        scope="Finite actual-triangle branch/arm pair checks. Free paths and complete30Hz native frames remain.",
    )
    (ROOT / "audit/split_tools_c_top_entry_native_branches_contacts.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print("SPLIT_TOOLS_TOP_ENTRY_NATIVE_BRANCHES", result["all_sections_have_individually_clear_branch"], flush=True)


if __name__ == "__main__":
    main()
