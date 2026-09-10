# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Author persistent OP030 parts, supports, tool use and bimanual routing [m, s]."""

import json
from copy import deepcopy
from functools import lru_cache

import numpy as np
from op020_jb_motion import grip_angle, mix, original, pose, weight
from op030_definition import (
    CX,
    CY,
    DOCK_Y,
    LIFT,
    M6_DOCK_X,
    M6_DOCK_Y,
    M6_EXTENSION,
    ROOT,
    TERMINAL_X,
    TERMINAL_Y,
    TERMINAL_Z,
    lug_frame,
    nut_supply_xy,
    product_frame,
    wire_route,
)
from scipy.spatial.transform import Rotation


def tool_for(frame, contact, orientation, gap):
    """Use the exact OP020 v11 replacement-tip calibration [m, rad]."""
    angle = grip_angle(round(gap - (0.00635 - 0.003), 8))
    middle = original.source_motion.pad_information(angle)[1] + [0, 0, 0.055]
    rotation = frame[:3, :3] @ orientation
    xyz = frame[:3, :3] @ contact + frame[:3, 3] - rotation @ middle
    return pose(rotation, xyz), angle / 0.8


SIDES = ("left", "right")
WORK = product_frame(lift=LIFT)
DOWN = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], dtype=float)
TIP_ROTATION = Rotation.from_euler("y", 140, degrees=True).as_matrix()
WIRE_GRASP_PITCH = 160
TOOL_CONTACT = pose(DOWN, (0, 0, 0.340))
ANGLE_CONTACT = pose(Rotation.from_euler("x", 180, degrees=True).as_matrix(), (0.340, 0, 0.033 + M6_EXTENSION))
DOCKS = {size: pose(location=(-0.65 + i * 0.11, DOCK_Y, 0.660)) for i, size in enumerate(("M4", "M6", "M14"))}
DOCKS["M6"] = pose(np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], dtype=float), (M6_DOCK_X, M6_DOCK_Y, 0.658))


@lru_cache(maxsize=1)
def angle_tool_paths():
    data = json.loads((ROOT / "data/op030_tool_paths_v02.json").read_text())
    assert all(not row["failures"] and row["carried_nut_included"] for row in data["routes"])
    return {row["wire"]: np.asarray(row["transforms"]) for row in data["routes"]}


def offset(frame, xyz):
    result = frame.copy()
    result[:3, 3] += xyz
    return result


def transit_actors(phase, side):
    """Return the rigid tool assembly carried during an unconstrained transit."""
    held = phase["before"]["holds"].get(side)
    if held is None or held[0] not in {"OP030_driver_M6", "OP030_driver_M14"}:
        return ()
    label = phase["label"]
    selected = label.endswith("／ナット供給へ")
    if held[0] == "OP030_driver_M6":
        selected |= label.endswith("／配線上方で工具姿勢を合わせる") or label == "M6工具を戻す／上方"
    if not selected:
        return ()
    nuts = tuple(name for name, (tool, _) in phase["before"]["driven_nuts"].items() if tool == held[0])
    return (held[0], *nuts)


def is_joint_transit(phase, side):
    """Identify free-hand or rigid-tool transport between fixed end poses."""
    moving = not np.allclose(phase["before"]["hands"][side], phase["after"]["hands"][side], atol=1e-8, rtol=0)
    empty = side not in phase["before"]["holds"] and any(
        token in phase["label"] for token in ("／退避", "／上方退避", "／進入")
    )
    return moving and (empty or bool(transit_actors(phase, side)))


def turn_frame(angle):
    rotation = Rotation.from_euler("z", angle).as_matrix()
    center = np.array([CX, CY, 0])
    return pose(rotation, center - rotation @ center)


def stock_wire(number):
    return pose(location=(-1.83, CY + (-0.07 if number == 1 else 0.30), 1.00))


def terminal_final(number):
    return WORK @ pose(location=(TERMINAL_X[number - 1], TERMINAL_Y, TERMINAL_Z))


def nut_final(name):
    if "_M4_" in name:
        number = int(name.split("_")[1][1:])
        sign = int(name.rsplit("_", 1)[1])
        return WORK @ pose(location=(TERMINAL_X[number - 1], TERMINAL_Y + sign * 0.034, TERMINAL_Z))
    number = int(name.split("_")[2])
    end = "J1" if "_J1_" in name else "T"
    result = WORK @ lug_frame(number, end)
    return result @ pose(location=(0, 0, 0.0038 if end == "J1" else 0.0032))


def initial_objects():
    objects = {
        "JB_OP020_UID001": product_frame(y=-2.85),
        "source_0292": pose(location=(0, -2.85, 0.439)),
        "OP030_lift_carriage": pose(location=(0, 0, -0.051)),
        "source_0672": pose(location=(0, -2.85, 0.392)),
        "OP030_supply_kit": pose(),
    }
    for number in (1, 2):
        objects[f"OP030_T{number:02d}_UID001"] = pose(location=(-2.08, -1.95 + (number - 1) * 0.11, 1.00))
        root = stock_wire(number)
        objects[f"OP030_H03_{number}_UID001"] = root
        objects[f"OP030_H03_{number}_UID001_T"] = root @ lug_frame(number, "T")
    objects.update({"OP030_driver_" + size: frame for size, frame in DOCKS.items()})
    nut_names = [f"OP030_T{n:02d}_M4_nut_{sign}" for n in (1, 2) for sign in (-1, 1)]
    nut_names += [f"OP030_H03_{n}_{end}_nut" for n in (1, 2) for end in ("J1", "T")]
    for i, name in enumerate(nut_names):
        objects[name] = pose(location=(*nut_supply_xy(i), 0.82))
        if "J1" in name:
            objects[name][:3, :3] = lug_frame(1, "J1")[:3, :3]
            objects[name][2, 3] += 0.006
    return objects


class Sequence:
    """A deterministic assembly schedule with explicit part/hand attachments."""

    def __init__(self):
        self.objects = initial_objects()
        self.hands = [pose(TIP_ROTATION, (-0.43, CY - 0.34, 1.35)), pose(TIP_ROTATION, (-0.43, CY + 0.34, 1.35))]
        self.gaps = [0.08, 0.08]
        self.holds = {}
        self.driven_nuts = {}
        self.yaw = np.pi / 2
        self.time = 0.0
        self.phases = []

    def snapshot(self):
        return deepcopy(
            dict(
                objects=self.objects,
                hands=self.hands,
                gaps=self.gaps,
                holds=self.holds,
                yaw=self.yaw,
                driven_nuts=self.driven_nuts,
            )
        )

    def phase(self, label, duration, *, objects=None, hands=None, gaps=None, turn=None, spin=None):
        start = self.snapshot()
        for name, matrix in (objects or {}).items():
            self.objects[name] = matrix.copy()
        for arm, frame in (hands or {}).items():
            self.hands[arm] = frame.copy()
        for arm, value in (gaps or {}).items():
            self.gaps[arm] = value
        if turn is not None:
            transform = turn_frame(turn)
            affected = {entry[0] for entry in self.holds.values()}
            # The free lug is an independent endpoint of the held wire.
            affected.update(name + "_T" for name in tuple(affected) if "H03" in name and name.endswith("UID001"))
            for name in affected:
                self.objects[name] = transform @ self.objects[name]
            self.hands = [transform @ hand for hand in self.hands]
            self.yaw += turn
        for arm, (name, relative) in self.holds.items():
            self.hands[arm] = self.objects[name] @ relative
        stop = self.snapshot()
        self.phases.append(
            dict(
                start=self.time, stop=self.time + duration, label=label, before=start, after=stop, turn=turn, spin=spin
            )
        )
        self.time += duration

    def hand_move(self, arm, target, label, duration=3.0, gap=None):
        self.phase(label, duration, hands={arm: target}, gaps={} if gap is None else {arm: gap})

    def grasp(self, arm, name, relative, gap, label):
        contact = self.objects[name] @ relative
        above = offset(contact, -contact[:3, 2] * 0.14)
        self.hand_move(arm, offset(self.hands[arm], (0, 0, 0.18)), label + "／上方退避", 1.5)
        self.hand_move(arm, above, label + "／進入", 3.0, min(gap + 0.006, 0.080))
        self.hand_move(arm, contact, label + "／接近", 1.5)
        self.hand_move(arm, contact, label + "／把持", 0.8, gap)
        self.holds[arm] = (name, relative.copy())

    def release(self, arm, label, *, gap=0.026):
        del self.holds[arm]
        contact = self.hands[arm].copy()
        self.hand_move(arm, contact, label + "／解放", 0.7, gap)
        self.hand_move(arm, offset(contact, -contact[:3, 2] * 0.14), label + "／抜け", 1.5)
        self.phase(label + "／開く", 0.5, gaps={arm: 0.080})

    def home(self, arm):
        base = pose(TIP_ROTATION, (-0.43, CY + (-0.34 if arm == 0 else 0.34), 1.35))
        return turn_frame(self.yaw - np.pi / 2) @ base

    def park(self, arm):
        self.hand_move(arm, self.home(arm), SIDES[arm] + "／退避", 3)

    def turn(self, angle, label):
        self.phase(label, 6.0, turn=angle)

    def get_tool(self, arm, size):
        name = "OP030_driver_" + size
        relative = ANGLE_CONTACT if size == "M6" else TOOL_CONTACT
        self.grasp(arm, name, relative, 0.048, size + "工具を把持")
        self.phase(size + "工具を取り出す", 1.8, objects={name: offset(self.objects[name], (0, 0, 0.20))})

    def return_tool(self, arm, size):
        name = "OP030_driver_" + size
        above = DOCKS[size].copy()
        above[2, 3] = 1.12
        self.phase(size + "工具を戻す／上方", 3, objects={name: above})
        self.phase(size + "工具を着座", 2, objects={name: DOCKS[size]})
        self.release(arm, size + "工具", gap=0.060)

    def fasten(self, arm, size, name, label):
        tool = "OP030_driver_" + size
        washer = {"M4": 0.0008, "M6": 0.0016, "M14": 0.0025}[size]
        mouth = washer + 0.0005
        # A hex nut permits a 180-degree equivalent socket orientation. Keep
        # the M4 tool body facing the same way as at its supply station; the
        # product frame itself is rotated 180 degrees around the vertical.
        yaw = -30 if size == "M6" else 180 if size == "M4" else 0
        alignment = pose(Rotation.from_euler("z", yaw, degrees=True).as_matrix())
        pickup = self.objects[name] @ pose(location=(0, 0, mouth))
        before_pickup = offset(pickup, pickup[:3, 2] * 0.080)
        self.phase(label + "／ナット供給へ", 2.5, objects={tool: offset(before_pickup, (0, 0, 0.14))})
        self.phase(label + "／供給ナットと同軸にする", 1.5, objects={tool: before_pickup})
        self.phase(label + "／ナットを保持", 2, objects={tool: pickup})
        self.driven_nuts[name] = (tool, pose(location=(0, 0, -mouth)))
        self.phase(label + "／取り上げ", 1.5, objects={tool: offset(pickup, (0, 0, 0.14))})
        seat = nut_final(name)
        travel = {"M4": 0.0091, "M6": 0.011, "M14": 0.022}[size]
        approach = seat @ alignment @ pose(location=(0, 0, mouth + travel))
        # Vertical clearance above the rim is established before lateral travel.
        self.phase(label + "／上方へ", 1.5, objects={tool: offset(self.objects[tool], (0, 0, 0.18))})
        if size == "M6":
            path = angle_tool_paths()[int(name.split("_")[2])]
            assert np.allclose(path[-1], approach, atol=1e-8)
            self.phase(label + "／配線上方で工具姿勢を合わせる", 3, objects={tool: path[0]})
            for index, frame in enumerate(path[1:], 1):
                previous = self.objects[tool]
                travel_m = np.linalg.norm(frame[:3, 3] - previous[:3, 3])
                angle = np.linalg.norm(Rotation.from_matrix(frame[:3, :3] @ previous[:3, :3].T).as_rotvec())
                duration = max(0.6, (travel_m + 0.15 * angle) / 0.070)
                self.phase(label + f"／配線を避けて進入{index}", duration, objects={tool: frame})
        else:
            self.phase(label + "／軸合わせ", 3, objects={tool: offset(approach, (0, 0, 0.16))})
            self.phase(label + "／ねじ先端の高さへ", 2.2, objects={tool: approach})
        pitch = {"M4": 0.0007, "M6": 0.001, "M14": 0.002}[size]
        self.phase(
            label + "／低速回転・着座",
            4.5,
            objects={tool: seat @ alignment @ pose(location=(0, 0, mouth))},
            spin=dict(tool=tool, nut=name, radians=-travel / pitch * 2 * np.pi),
        )
        self.objects[name] = seat @ alignment
        del self.driven_nuts[name]
        withdrawal = 0.011 if size == "M6" else 0.08
        self.phase(
            label + "／工具を軸方向へ抜く", 1.5, objects={tool: offset(self.objects[tool], seat[:3, 2] * withdrawal)}
        )
        if size == "M6":
            for index, frame in enumerate(path[-2::-1], 1):
                previous = self.objects[tool]
                travel_m = np.linalg.norm(frame[:3, 3] - previous[:3, 3])
                angle = np.linalg.norm(Rotation.from_matrix(frame[:3, :3] @ previous[:3, :3].T).as_rotvec())
                duration = max(0.6, (travel_m + 0.15 * angle) / 0.070)
                self.phase(label + f"／配線を避けて抜き取る{index}", duration, objects={tool: frame})
        else:
            self.phase(label + "／工具を上げる", 1.5, objects={tool: offset(self.objects[tool], (0, 0, 0.16))})


def build_sequence():
    seq = Sequence()
    seq.phase(
        "OP020の位置決めを解除しローラーへ着座",
        2,
        objects={
            "JB_OP020_UID001": product_frame(y=-2.85, lift=-0.014),
            "source_0292": pose(location=(0, -2.85, 0.425)),
            "source_0672": pose(location=(0, -2.85, 0.378)),
        },
    )
    seq.phase(
        "OP020完了品を同じパレットで搬入",
        6,
        objects={"JB_OP020_UID001": product_frame(lift=-0.014), "source_0292": pose(location=(0, CY, 0.425))},
    )
    seq.phase("OP030の位置決めピンを差し込む", 1.5, objects={"OP030_lift_carriage": pose(location=(0, 0, -0.014))})
    seq.phase(
        "位置決め完了・14 mm座上げ",
        1.5,
        objects={
            "JB_OP020_UID001": product_frame(),
            "source_0292": pose(location=(0, CY, 0.439)),
            "OP030_lift_carriage": pose(),
        },
    )
    seq.phase(
        "停止・位置決め／350 mm上昇",
        4,
        objects={
            "JB_OP020_UID001": WORK,
            "source_0292": pose(location=(0, CY, 0.439 + LIFT)),
            "OP030_lift_carriage": pose(location=(0, 0, LIFT)),
        },
    )
    seq.phase("作業域と供給状態を確認する姿勢", 1)
    supplied = {
        name: offset(matrix, (0.34, 0, 0))
        for name, matrix in seq.objects.items()
        if (name.startswith("OP030_T") and name.endswith("UID001"))
        or (name.startswith("OP030_H03_") and "UID001" in name)
    }
    supplied["OP030_supply_kit"] = pose(location=(0.34, 0, 0))
    seq.phase("選択キットを340 mm引き出す", 2.5, objects=supplied)
    for number in (1, 2):
        seq.park(0)
        seq.park(1)
        seq.turn(-np.pi, f"T{number:02d}供給へ旋回")
        name = f"OP030_T{number:02d}_UID001"
        # Both flat pads close along the disc's X axis; mounting ears remain at Y.
        relative = pose(Rotation.from_euler("z", 45, degrees=True).as_matrix() @ DOWN, (0, 0, 0.016))
        seq.grasp(1, name, relative, 0.052, f"T{number:02d}絶縁支持部")
        seq.phase(f"T{number:02d}を棚から持ち上げる", 2, objects={name: offset(seq.objects[name], (0, 0, 0.40))})
        seq.turn(np.pi, f"T{number:02d}保持で作業側へ")
        final = terminal_final(number)
        seq.phase(f"T{number:02d}／2本の取付スタッドへ位置合わせ", 3, objects={name: offset(final, (0, 0, 0.18))})
        seq.phase(f"T{number:02d}／支持部を着座", 2.5, objects={name: final})
        seq.release(1, f"T{number:02d}／2本のスタッドと支持面へ支持移管", gap=0.060)
        seq.park(1)
        seq.get_tool(0, "M4")
        for sign in (-1, 1):
            seq.fasten(0, "M4", f"OP030_T{number:02d}_M4_nut_{sign}", f"T{number:02d}取付ナット{sign:+d}")
        seq.return_tool(0, "M4")
    # Lower internal route first; the upper wire is then placed above it.
    for number in (2, 1):
        seq.park(0)
        seq.park(1)
        seq.turn(-np.pi, f"H03-{number}供給へ旋回")
        name = f"OP030_H03_{number}_UID001"
        end = name + "_T"
        local_right = lug_frame(number, "J1") @ pose(location=(0.020, 0, 0.017))
        # Grasp rotations are defined at the final working posture, then rotate
        # with the same physical component during the complete stock transfer.
        local_right[:3, :3] = WORK[:3, :3].T @ Rotation.from_euler("y", WIRE_GRASP_PITCH, degrees=True).as_matrix()
        route = wire_route(number)
        local_points = (route - lug_frame(number, "T")[:3, 3]) @ lug_frame(number, "T")[:3, :3]
        contact_index = np.argmin(abs(local_points[-30:, 0] - 0.068)) + len(route) - 30
        local_left = pose(location=local_points[contact_index])
        local_left[:3, :3] = (WORK @ lug_frame(number, "T"))[:3, :3].T @ Rotation.from_euler(
            "y", 180, degrees=True
        ).as_matrix()
        seq.grasp(1, name, local_right, 0.016, f"H03-{number}／J1側圧着部")
        seq.grasp(0, end, local_left, 0.014, f"H03-{number}／内部端子側の絶縁線")
        seq.phase(
            f"H03-{number}／両端を保持して持ち上げる",
            2.5,
            objects={name: offset(seq.objects[name], (0, 0, 0.40)), end: offset(seq.objects[end], (0, 0, 0.40))},
        )
        if number == 1:
            seq.phase("空キットをストッカへ戻す", 2.5, objects={"OP030_supply_kit": pose()})
        seq.turn(np.pi, f"H03-{number}／両腕保持で作業側へ")
        root_approach = WORK @ pose(location=(0.04, 0, 0))
        end_approach = root_approach @ pose(location=(0, 0, 0.04)) @ lug_frame(number, "T")
        seq.phase(
            f"H03-{number}／筐体上方へ",
            3,
            objects={name: offset(root_approach, (0, 0, 0.20)), end: offset(end_approach, (0, 0, 0.20))},
        )
        seq.phase(f"H03-{number}／J1背面の高さへ合わせる", 2.5, objects={name: root_approach, end: end_approach})
        seq.phase(
            f"H03-{number}／両端を支持してM6スタッドへ軸方向に差し込む",
            2.5,
            objects={name: WORK, end: offset(WORK @ lug_frame(number, "T"), (0, 0, 0.04))},
        )
        seq.phase(f"H03-{number}／丸形端子をM14スタッドへ下ろす", 2.5, objects={end: WORK @ lug_frame(number, "T")})
        seq.release(1, f"H03-{number}／J1スタッドと端子受けへ支持移管", gap=0.017)
        seq.hand_move(1, offset(seq.hands[1], (0, 0.20, 0.15)), f"H03-{number}／右手を外側上方へ移す", 3)
        seq.release(0, f"H03-{number}／回り止め受けへ支持移管", gap=0.023)
        seq.park(0)
        seq.park(1)
        seq.get_tool(0, "M6")
        seq.fasten(0, "M6", f"OP030_H03_{number}_J1_nut", f"H03-{number}／J1背面接続")
        seq.return_tool(0, "M6")
        seq.get_tool(0, "M14")
        seq.fasten(0, "M14", f"OP030_H03_{number}_T_nut", f"H03-{number}／T{number:02d}電気接続")
        seq.return_tool(0, "M14")
    seq.park(0)
    seq.park(1)
    seq.phase("2本・4か所の接続状態を確認する姿勢", 3)
    assembled = [
        name
        for name in seq.objects
        if name in ("JB_OP020_UID001", "source_0292", "OP030_lift_carriage")
        or (name.startswith(("OP030_T", "OP030_H03_")) and ("UID001" in name or "_nut" in name))
    ]
    seq.phase(
        "両腕退避後に作業リフトを下ろす",
        4,
        objects={name: offset(seq.objects[name], (0, 0, -LIFT)) for name in assembled},
    )
    return seq


def evaluate_phase(phase, t):
    before, after = phase["before"], phase["after"]
    w = weight(t, phase["start"], phase["stop"])
    result = dict(
        objects={k: mix(v, after["objects"][k], w) for k, v in before["objects"].items()},
        hands=[mix(a, b, w) for a, b in zip(before["hands"], after["hands"], strict=True)],
        gaps=np.array(before["gaps"]) * (1 - w) + np.array(after["gaps"]) * w,
        yaw=before["yaw"] * (1 - w) + after["yaw"] * w,
    )
    if phase["turn"] is not None:
        transform = turn_frame(phase["turn"] * w)
        affected = {value[0] for value in before["holds"].values()}
        affected.update(name + "_T" for name in tuple(affected) if "H03" in name and name.endswith("UID001"))
        for name in affected:
            result["objects"][name] = transform @ before["objects"][name]
        result["hands"] = [transform @ frame for frame in before["hands"]]
    for name, (tool, relative) in before["driven_nuts"].items():
        result["objects"][name] = result["objects"][tool] @ relative
    if phase["spin"]:
        driven = phase["spin"]
        result["objects"][driven["nut"]] = result["objects"][driven["nut"]] @ pose(
            Rotation.from_euler("z", driven["radians"] * w).as_matrix()
        )
    for arm, (name, relative) in before["holds"].items():
        result["hands"][arm] = result["objects"][name] @ relative
    result["tools"] = np.array(
        [
            tool_for(np.eye(4), hand[:3, 3], hand[:3, :3], float(gap))[0]
            for hand, gap in zip(result["hands"], result["gaps"], strict=True)
        ]
    )
    result["grips"] = np.array(
        [
            tool_for(np.eye(4), hand[:3, 3], hand[:3, :3], float(gap))[1]
            for hand, gap in zip(result["hands"], result["gaps"], strict=True)
        ]
    )
    result["root"] = pose(Rotation.from_euler("z", result["yaw"]).as_matrix(), (CX, CY, 0))
    return result
