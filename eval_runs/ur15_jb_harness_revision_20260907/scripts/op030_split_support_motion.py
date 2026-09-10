# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""ST A support placement with a permanent left-arm M4 spindle [m, rad, s]."""

import json

import numpy as np
from op030_definition import CY, LIFT, ROOT, pose, product_frame
from op030_motion import DOWN, Sequence, is_joint_transit, offset, terminal_final, turn_frame
from op030_split_tools import driver_flange_to_tcp
from scipy.spatial.transform import Rotation


class SupportSequence(Sequence):
    """Retain the old support pick calibration and explicit persistent IDs."""

    def __init__(self):
        super().__init__()
        self.objects = {
            "JB_OP020_UID001": product_frame(lift=LIFT),
            "source_0292": pose(location=(0, CY, 0.439 + LIFT)),
            "OP030_lift_carriage": pose(location=(0, 0, LIFT)),
            "OP030_supply_kit": pose(),
        }
        layout = json.loads((ROOT / "audit/op030_split_layout_v03.json").read_text())
        self.grid = layout["support_supply"]["records"]
        for row in self.grid:
            self.objects[row["uid"]] = pose(location=row["stock_cell_m"])
        self.driver_sizes = {0: "M4"}
        self.driver_names = {0: "OP030A_driver_M4"}
        driver = self.driver_names[0]
        self.objects[driver] = self.driver_home(0)
        self.holds[0] = (driver, np.linalg.inv(driver_flange_to_tcp("M4")))
        self.hands[0] = self.objects[driver] @ self.holds[0][1]

    def driver_home(self, arm):
        """Return the candidate socket park pose at the current torso yaw [m]."""
        matrix = pose(location=(-0.55, CY - 0.72, 1.30))
        return turn_frame(self.yaw - np.pi / 2) @ matrix

    def park(self, arm):
        if arm in self.driver_sizes:
            self.phase("OP030A／固定M4工具を待機位置へ", 4, objects={self.driver_names[arm]: self.driver_home(arm)})
        else:
            super().park(arm)

    def evaluate(self, time):
        """Return local-cell target poses [m, rad] at time [s]."""
        from op030_split_fastening_motion import evaluate_fixed_phase

        phase = next((phase for phase in self.phases if time <= phase["stop"] + 1e-9), self.phases[-1])
        result = evaluate_fixed_phase(self, phase, time)
        result["free"][1] |= is_joint_transit(phase, 1)
        if phase["label"] == "OP030A／固定M4工具を待機位置へ":
            result["free"][0] = True
        result["label"] = phase["label"]
        return result


def build_sequence():
    """Author two support picks and four automatically presented M4 bolts."""
    from op030_split_fastening_motion import append_fastening, configure_feeders

    seq = SupportSequence()
    configure_feeders(seq, "A")
    seq.phase("OP030A／20個格子供給・本体位置決め済み", 2)
    supplied = {row["uid"]: offset(seq.objects[row["uid"]], (0.34, 0, 0)) for row in seq.grid}
    supplied["OP030_supply_kit"] = pose(location=(0.34, 0, 0))
    seq.phase("OP030A／支持部品パレットを340mm引出す", 2.5, objects=supplied)
    for number in (1, 2):
        seq.park(0)
        seq.park(1)
        seq.turn(-np.pi, f"T{number:02d}／供給側へ旋回")
        name = f"OP030_T{number:02d}_UID001"
        relative = pose(Rotation.from_euler("z", 45, degrees=True).as_matrix() @ DOWN, (0, 0, 0.016))
        seq.grasp(1, name, relative, 0.052, f"T{number:02d}／絶縁支持部を把持")
        seq.phase(f"T{number:02d}／格子パレットから持上げ", 3, objects={name: offset(seq.objects[name], (0, 0, 0.40))})
        seq.turn(np.pi, f"T{number:02d}／保持して組付側へ旋回")
        final = terminal_final(number)
        seq.phase(f"T{number:02d}／取付穴の位置合わせ", 4, objects={name: offset(final, (0, 0, 0.18))})
        seq.phase(f"T{number:02d}／支持面へ着座", 3, objects={name: final})
        seq.release(1, f"T{number:02d}／支持面へ移管", gap=0.060)
        seq.park(1)
        for sign in (-1, 1):
            seat = final @ pose(location=(0, sign * 0.034, 0))
            append_fastening(seq, 0, "M4", seat, label=f"T{number:02d}／M4取付ボルト{sign:+d}")
    seq.park(0)
    seq.park(1)
    remaining = {
        row["uid"]: pose(location=row["stock_cell_m"])
        for row in seq.grid
        if row["uid"] not in {"OP030_T01_UID001", "OP030_T02_UID001"}
    }
    remaining["OP030_supply_kit"] = pose()
    seq.phase("OP030A／残18個のパレットを戻す", 2.5, objects=remaining)
    seq.phase("OP030A／支持部2個・取付ボルト4本の組付完了", 2)
    return seq
