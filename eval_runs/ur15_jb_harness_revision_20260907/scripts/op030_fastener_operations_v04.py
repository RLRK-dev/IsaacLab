# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Separate fixed-tool pickup and driving with finite ownership records [m, s].

Reuses the v03 presenter, fixed TCPs, feed phases and thread advance. The old
append_fastening API and its saved factories are unchanged.
"""

from dataclasses import dataclass

import numpy as np
from op030_definition import pose
from op030_motion import Sequence, offset
from op030_split_fastening_motion import _phase, _spindle_angles
from op030_split_tools import SIZES, fastener_socket_offset, feeder_queue_poses
from scipy.spatial.transform import Rotation


@dataclass(frozen=True)
class FastenerPickup:
    """A persistent fastener held by one fixed spindle [m, s]."""

    uid: str
    arm: int
    size: str
    kind: str
    driver: str
    mouth_m: float
    start_s: float
    receive_start_s: float
    attach_s: float
    clear_s: float


def fastener_ledger_initialize(seq: Sequence) -> None:
    """Initialize finite supply ownership before any pickup [s]."""
    if hasattr(seq, "fastener_events"):
        return
    seq.fastener_events = []
    seq.tool_fasteners = {}
    seq.fastener_initial_owners = {
        uid: dict(owner="supply", feeder=spec["name"], size=size)
        for size, spec in seq.feeder_specs.items()
        for uid in spec["uids"]
    }


def fastener_ledger_at(seq: Sequence, time: float) -> dict:
    """Return physical UID owners and supply/tool/product counts at time [s]."""
    owners = {uid: dict(value) for uid, value in seq.fastener_initial_owners.items()}
    for event in seq.fastener_events:
        if event["time_s"] <= time + 1e-10:
            owners[event["uid"]] = dict(event["state"])
    counts = {}
    for state in owners.values():
        row = counts.setdefault(state["size"], dict(supply=0, tool=0, installed=0))
        row[state["owner"]] += 1
    return dict(owners=owners, counts=counts)


def fastener_pickup_append(
    seq: Sequence, arm: int, size: str, *, uid: str | None = None, label: str = ""
) -> FastenerPickup:
    """Append the existing single-file feed and pickup, ending clear of the nest [m, s]."""
    fastener_ledger_initialize(seq)
    if arm in seq.tool_fasteners or seq.driver_sizes.get(arm) != size:
        raise ValueError("Pickup needs an empty compatible fixed tool")
    spec = seq.feeder_specs[size]
    used = spec["consumed"]
    if used >= spec["count"]:
        raise ValueError("Finite presenter exhausted")
    expected = spec["uids"][used]
    if uid is not None and uid != expected:
        raise ValueError("Only the next physical queue UID can be picked")
    uid = expected
    driver, start, first_phase = seq.driver_names[arm], seq.time, len(seq.phases)
    label = label or f"{size}／自動補充"
    world = spec["world"]
    gate = spec["name"] + "_escapement"
    if used:
        _phase(seq, label + "／切出しゲートを開く", 0.5, arm, objects={gate: world @ pose(location=(0, 0.045, 0))})
        presented = {
            name: world @ frame
            for name, frame in zip(spec["uids"], feeder_queue_poses(size, spec["count"], used, 1), strict=True)
            if frame is not None
        }
        _phase(seq, label + "／単列供給を1個分送る", 1.0, arm, objects=presented)
        _phase(seq, label + "／次部品を切出して停止", 0.5, arm, objects={gate: world})
    else:
        _phase(seq, label + "／供給ユニットの先頭部品を確認", 0.6, arm)
    mouth = fastener_socket_offset(size, spec["kind"])
    pickup = world @ pose(location=(0, 0, mouth))
    above = pickup @ pose(location=(0, 0, 0.080))
    _phase(seq, label + "／固定工具を供給上方へ", 4.0, arm, offset(above, (0, 0, 0.15)), free=True)
    receive_start = seq.time
    _phase(seq, label + "／取得座と同軸に合わせる", 2.0, arm, above)
    _phase(seq, label + "／ソケットで先頭部品を保持", 2.0, arm, pickup)
    attach = seq.time
    relative = pose(location=(0, 0, -mouth))
    seq.driven_nuts[uid] = (driver, relative)
    seq.fastener_events.append(
        dict(time_s=attach, uid=uid, state=dict(owner="tool", arm=arm, driver=driver, size=size))
    )
    _phase(seq, label + "／同じ部品を取得座から引き上げる", 2.0, arm, offset(pickup, (0, 0, 0.14)))
    spec["consumed"] += 1  # Compatibility: v03 consumed means picked from presenter.
    _phase(seq, label + "／工具を搬送高さへ", 2.0, arm, offset(seq.objects[driver], (0, 0, 0.16)))
    receipt = FastenerPickup(uid, arm, size, spec["kind"], driver, mouth, start, receive_start, attach, seq.time)
    seq.tool_fasteners[arm] = receipt
    for phase in seq.phases[first_phase:]:
        phase["fastener_operation"] = dict(kind="pickup", arm=arm, uid=uid)
    return receipt


def fastener_drive_append(seq: Sequence, pickup: FastenerPickup, seat: np.ndarray, *, label: str = "") -> dict:
    """Drive the held straight-tool fastener and withdraw before another pickup [m, rad, s]."""
    arm, size, uid, driver = pickup.arm, pickup.size, pickup.uid, pickup.driver
    if seq.tool_fasteners.get(arm) != pickup or uid not in seq.driven_nuts:
        raise ValueError("Driving needs the same fastener currently held by this tool")
    label = label or f"{size}／固定工具で締結"
    first_phase, start = len(seq.phases), seq.time
    alignment = pose(Rotation.from_euler("z", 180 if size == "M4" else 0, degrees=True).as_matrix())
    travel = {"M4": 0.0092, "M6": 0.011, "M14": 0.022}[size]
    approach = seat @ alignment @ pose(location=(0, 0, pickup.mouth_m + travel))
    _phase(seq, label + "／固定工具を締結部上方へ", 4.0, arm, offset(approach, (0, 0, 0.17)), free=True)
    if size == "M4":
        _phase(
            seq,
            label + "／ボルト先端を取付耳の穴へ",
            2.0,
            arm,
            seat @ alignment @ pose(location=(0, 0, pickup.mouth_m + 0.0152)),
        )
        _phase(seq, label + "／耳の貫通穴を通してインサートへ", 1.5, arm, approach)
    else:
        _phase(seq, label + "／スタッド先端と同軸にする", 2.2, arm, approach)
    radians = -travel / SIZES[size]["pitch"] * 2 * np.pi
    seated = seat @ alignment @ pose(location=(0, 0, pickup.mouth_m))
    _phase(seq, label + "／低速ねじ進行・着座", 6.0, arm, seated, spin=dict(tool=driver, nut=uid, radians=radians))
    seq.objects[uid] = seat @ alignment @ pose(Rotation.from_euler("z", radians).as_matrix())
    del seq.driven_nuts[uid]
    del seq.tool_fasteners[arm]
    empty = seq.time
    seq.fastener_events.append(dict(time_s=empty, uid=uid, state=dict(owner="installed", size=size)))
    _phase(seq, label + "／保持を解除して軸方向へ退避", 1.8, arm, offset(seated, seat[:3, 2] * 0.080))
    _phase(seq, label + "／次工程のため上方退避", 2.0, arm, offset(seq.objects[driver], (0, 0, 0.16)))
    angle = _spindle_angles(seq, seq.time)[arm]
    reset = -float(np.arctan2(np.sin(angle), np.cos(angle)))
    _phase(seq, label + "／空ソケットを供給基準へ戻す", 1.0, arm)
    seq.phases[-1]["spindle_reset"] = dict(arm=arm, radians=reset)
    for phase in seq.phases[first_phase:]:
        phase["fastener_operation"] = dict(kind="drive", arm=arm, uid=uid)
    return dict(uid=uid, arm=arm, start_s=start, tool_empty_s=empty, tool_clear_s=seq.time)
