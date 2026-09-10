# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""ST A holds each support through fastening and overlaps initial pickup [m, s]."""

import numpy as np
from op030_definition import pose
from op030_fastener_operations_v04 import (
    fastener_drive_append,
    fastener_ledger_at,
    fastener_ledger_initialize,
    fastener_pickup_append,
)
from op030_motion import DOWN, mix, offset, terminal_final, tool_for, weight
from op030_split_fastening_motion import configure_feeders
from op030_split_support_motion import SupportSequence
from scipy.spatial.transform import Rotation


class SupportSequenceV04(SupportSequence):
    """Evaluate concurrent constrained arm tracks on one world clock [m, rad, s]."""

    def __init__(self):
        super().__init__()
        self.objects.pop("OP030_lift_carriage", None)
        self.parallel_placements = []
        self.support_hold_intervals = []
        self.station_pallet_z_m = 0.789
        self.station_product_z_m = 0.8845
        # The exported molded faces lie at ±26.20003948 mm. Match their
        # measured span on the reused gripper calibration's 10 nm grid.
        self.support_grasp_gap_m = 0.05240008
        self.support_grasp_height_m = 0.01585
        self.support_grasp_tilt_degrees = 60.0

    @staticmethod
    def placement_pose(track: dict, time: float) -> np.ndarray:
        """Evaluate original four-second alignment and three-second seating [m, s]."""
        if time <= track["align_stop_s"]:
            fraction = (time - track["start_s"]) / (track["align_stop_s"] - track["start_s"])
            return mix(track["initial"], track["above"], weight(fraction, 0, 1))
        fraction = (time - track["align_stop_s"]) / (track["seat_stop_s"] - track["align_stop_s"])
        return mix(track["above"], track["final"], weight(fraction, 0, 1))

    def evaluate(self, time: float) -> dict:
        """Return both actual-time targets, finite ownership and attachment states [m, rad, s]."""
        result = super().evaluate(time)
        for track in self.parallel_placements:
            if track["start_s"] - 1e-9 <= time <= track["stop_s"] + 1e-9:
                frame = self.placement_pose(track, time)
                result["objects"][track["uid"]] = frame
                contact = frame @ track["relative"]
                result["tools"][1], result["grips"][1] = tool_for(
                    np.eye(4), contact[:3, 3], contact[:3, :3], track["gap_m"]
                )
                result["free"][1] = False
                step = "位置合わせ" if time < track["align_stop_s"] else "着座・保持"
                result["label"] += f" ＋ {track['uid'].split('_')[1]}／右フィンガで{step}"
        result["ledger"] = fastener_ledger_at(self, time)
        return result


def support_sequence_v04() -> SupportSequenceV04:
    """Author fixed-height support assembly and next-cycle M4 prefill [m, s]."""
    seq = SupportSequenceV04()
    configure_feeders(seq, "A")
    fastener_ledger_initialize(seq)
    seq.phase("OP030A／固定高さ789mm・本体位置決め済み", 2)
    supplied = {row["uid"]: offset(seq.objects[row["uid"]], (0.34, 0, 0)) for row in seq.grid}
    supplied["OP030_supply_kit"] = pose(location=(0.34, 0, 0))
    seq.phase("OP030A／支持部品パレットを340mm引出す", 2.5, objects=supplied)
    for number in (1, 2):
        seq.park(0)
        seq.park(1)
        seq.turn(-np.pi, f"T{number:02d}／供給側へ旋回")
        name = f"OP030_T{number:02d}_UID001"
        relative = pose(
            DOWN @ Rotation.from_euler("y", seq.support_grasp_tilt_degrees, degrees=True).as_matrix(),
            (0, 0, seq.support_grasp_height_m),
        )
        seq.grasp(1, name, relative, seq.support_grasp_gap_m, f"T{number:02d}／対向マーク面で絶縁支持部を把持")
        grasp_time = seq.time
        seq.phase(f"T{number:02d}／格子パレットから持上げ", 3, objects={name: offset(seq.objects[name], (0, 0, 0.40))})
        seq.turn(np.pi, f"T{number:02d}／保持して組付側へ旋回")
        initial, final = seq.objects[name].copy(), terminal_final(number)
        receipt = fastener_pickup_append(seq, 0, "M4", label=f"T{number:02d}／設置と並行してM4を受取る")
        track = dict(
            uid=name,
            start_s=receipt.receive_start_s,
            align_stop_s=receipt.receive_start_s + 4,
            seat_stop_s=receipt.receive_start_s + 7,
            stop_s=receipt.clear_s,
            initial=initial,
            above=offset(final, (0, 0, 0.18)),
            final=final,
            relative=relative,
            gap_m=seq.support_grasp_gap_m,
        )
        seq.parallel_placements.append(track)
        # Phase snapshots also follow the right track. Evaluation retains the
        # original uninterrupted quintic laws rather than restarting at each
        # independent two-second left-tool boundary.
        for phase in seq.phases:
            if phase["stop"] <= track["start_s"] or phase["start"] >= track["stop_s"]:
                continue
            for field, at in (("before", phase["start"]), ("after", phase["stop"])):
                frame = seq.placement_pose(track, at)
                phase[field]["objects"][name] = frame
                phase[field]["hands"][1] = frame @ relative
        seq.objects[name] = final.copy()
        seq.hands[1] = final @ relative
        fasteners = []
        for index, sign in enumerate((-1, 1)):
            if index:
                receipt = fastener_pickup_append(seq, 0, "M4", label=f"T{number:02d}／右保持中に2本目を補充")
            seat = final @ pose(location=(0, sign * 0.034, 0))
            fasteners.append(
                fastener_drive_append(seq, receipt, seat, label=f"T{number:02d}／右保持のままM4{sign:+d}締結")
            )
        seq.park(0)
        release_time = seq.time
        seq.release(1, f"T{number:02d}／2本締結・左工具退避後に支持を解放", gap=0.060)
        seq.park(1)
        seq.support_hold_intervals.append(
            dict(uid=name, grasp_s=grasp_time, seat_s=track["seat_stop_s"], release_s=release_time, fasteners=fasteners)
        )
    remaining = {
        row["uid"]: pose(location=row["stock_cell_m"])
        for row in seq.grid
        if row["uid"] not in {"OP030_T01_UID001", "OP030_T02_UID001"}
    }
    remaining["OP030_supply_kit"] = pose()
    seq.phase("OP030A／残18個のパレットを戻す", 2.5, objects=remaining)
    seq.phase("OP030A／支持部2個・取付ボルト4本の組付完了", 1)
    seq.work_complete_author_time_s = seq.time
    fastener_pickup_append(seq, 0, "M4", label="OP030A／次サイクル用M4を自動補充")
    seq.park(0)
    seq.phase("OP030A／次サイクル用1本を保持して待機", 1)
    seq.assembled_uids = tuple(event["uid"] for event in seq.fastener_events if event["state"]["owner"] == "installed")
    seq.end_loaded_uids = tuple(receipt.uid for receipt in seq.tool_fasteners.values())
    return seq
