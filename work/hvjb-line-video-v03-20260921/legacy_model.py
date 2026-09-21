# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Author a scale-free whole-line motion explanation; it is not a robot program."""

from __future__ import annotations

import hashlib
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
import numpy as np
import pyrender

HELPERS = Path("/home/rlrk/src/ur15-line-render")
REFERENCE = Path("/home/rlrk/IsaacLab-op040/eval_runs/ur15_jb_harness_revision_20260907")
sys.path.insert(0, str(HELPERS))
from render_ur15_line import (  # noqa: E402
    box_mesh,
    cylinder_between_pose,
    cylinder_mesh,
    look_at,
    material,
    sphere_mesh,
    transform,
)

ROOT = Path(__file__).resolve().parent
FPS, DURATION = 15, 86
WIDTH, HEIGHT = 1280, 720
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BLUE = material((0.15, 0.44, 0.64, 1), roughness=0.6)
CYAN = material((0.15, 0.64, 0.82, 1), roughness=0.65)
SILVER = material((0.48, 0.60, 0.68, 1), metallic=0.1)
WHITE = material((0.70, 0.78, 0.83, 1))
DARK = material((0.13, 0.18, 0.22, 1))
ORANGE = material((0.95, 0.34, 0.055, 1))
GREEN = material((0.22, 0.50, 0.38, 1))
AMBER = material((0.73, 0.48, 0.15, 1))
HIDDEN = np.array([0, 0, -30.0])
STAGES = [
    (0, 4, "全体", "1段往復コンベア＋筐体・完成品の共用20枠｜配置・寸法は仮置き"),
    (4, 11, "供給", "OP010｜指を閉じて筐体を持上げ、パレットへ載せて開く"),
    (11, 22, "A/B", "A/B外組み｜部品を置き、フィンガで保持したまま工具が締結"),
    (22, 29, "合流A", "AからCへ｜台で本体を受け、自由端の保持をC補助へ引き継ぐ"),
    (29, 35, "合流B", "BからCへ｜共用補助が配線を案内し、C主担当へ本体を渡す"),
    (35, 40, "一体化", "Cで保持・固定・持ち替え｜A/Bは次ワークを並行して準備"),
    (40, 48, "搭載", "C｜主担当がユニットを運び、2つの補助役が自由端を案内する案"),
    (48, 55, "ヘッダー", "C｜内側端末を案内・保持し、外側ヘッダーを取り付けて締結"),
    (55, 62, "残接続", "C｜導体とケーブルを保持して締結。工具退避後に指を開いて上昇"),
    (62, 69, "後工程", "後工程｜検査・蓋・シール設備の仮動作（順序と設備分担は未定）"),
    (69, 74, "同じ段を復路搬送", "1段式コンベア｜完成品を載せたパレットを供給側へ戻す"),
    (74, 82, "空き枠へ収納", "共用XYZ｜完成品を取り出し、空筐体があった同じ枠01へ戻す"),
    (82, 86, "全体", "20枠を共用：完成品1枠＋未使用筐体19枠。パレットは同じ段で往復"),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sample(t, keys):
    if t <= keys[0][0]:
        return np.asarray(keys[0][1], dtype=float)
    for (ta, a), (tb, b) in zip(keys, keys[1:]):
        if t <= tb:
            u = (t - ta) / (tb - ta)
            u = u * u * (3 - 2 * u)
            return np.asarray(a, dtype=float) * (1 - u) + np.asarray(b, dtype=float) * u
    return np.asarray(keys[-1][1], dtype=float)


class Model:
    def __init__(self):
        self.scene = pyrender.Scene(bg_color=(0.92, 0.95, 0.97, 1), ambient_light=(0.42, 0.42, 0.42))
        self.dynamic = []
        self.names = []
        self.static = []
        self.unit_cylinder = cylinder_mesh(1, 1, SILVER, sections=14)
        self.wire_cylinder = cylinder_mesh(1, 1, ORANGE, sections=10)
        self.joint_mesh = sphere_mesh(0.085, DARK)
        self.build_environment()
        self.arms = {}
        for name, base, elbow_side in (
            ("A", (-2.25, 1.62, 0), -1),
            ("B", (2.25, 1.62, 0), 1),
            ("AB補助", (0, 2.15, 0), 1),
            ("C主", (-1.40, -2.17, 0), -1),
            ("C補助", (1.40, -2.17, 0), 1),
        ):
            self.arms[name] = self.build_arm(name, base, elbow_side)
        self.case = self.build_case("case")
        self.stock_cases = []
        for r in range(5):
            for c in range(4):
                p = np.array([-4.7 - c * 0.90, -0.15 + r * 0.60, 0.855])
                parts = self.build_case(f"stock_{r}_{c}")
                self.group(parts, p)
                self.stock_cases.append(parts)
                self.add_box(
                    f"stock_slot_{r}_{c}",
                    (0.82, 0.52, 0.015),
                    GREEN if (r, c) == (0, 0) else SILVER,
                    p + [0, 0, -0.025],
                    False,
                )
        self.a_unit = self.build_unit("base", panel=False)
        self.b_unit = self.build_unit("panel", panel=True)
        self.a_next = self.build_unit("base_next", panel=False)
        self.b_next = self.build_unit("panel_next", panel=True)
        self.header = self.build_header()
        self.lid = self.add_box("lid", (0.73, 0.44, 0.025), WHITE, HIDDEN)
        self.busbar = self.add_box("busbar", (0.31, 0.08, 0.025), SILVER, HIDDEN)
        self.part_a = self.add_cylinder("contactor", 0.075, 0.12, DARK, HIDDEN)
        self.pallet = self.add_box("pallet", (0.88, 0.57, 0.055), SILVER, (-3.7, -1.2, 0.80))
        self.xyz = [
            self.add_box("infeed_carriage", (0.24, 0.20, 0.16), BLUE, HIDDEN),
            self.add_box("infeed_z", (0.055, 0.055, 1), SILVER, HIDDEN),
            self.add_box("infeed_y_bridge", (5.0, 0.085, 0.08), SILVER, HIDDEN),
        ]
        self.xyz_hand = self.build_hand("infeed")
        self.out_xyz = [
            self.add_box("outfeed_carriage", (0.24, 0.20, 0.16), AMBER, HIDDEN),
            self.add_box("outfeed_z", (0.055, 0.055, 1), SILVER, HIDDEN),
            self.add_box("outfeed_y_bridge", (1.7, 0.085, 0.08), SILVER, HIDDEN),
        ]
        self.out_hand = self.build_hand("outfeed")
        self.tools = {}
        for name, xy in (("A", (-1.55, 0.85)), ("B", (1.55, 0.85)), ("C", (0.0, 0.37))):
            self.tools[name] = (
                self.add_box(f"tool_{name}", (0.15, 0.15, 0.26), WHITE, (*xy, 1.7)),
                self.add_cylinder(f"bit_{name}", 0.014, 0.30, SILVER, (*xy, 1.42)),
            )
        self.probe = self.add_box("test_probe", (0.43, 0.22, 0.09), AMBER, HIDDEN)
        self.wires = []
        for group in ("A", "B"):
            pieces = [self.node(f"wire_{group}_{i}", self.wire_cylinder) for i in range(14)]
            sleeve = self.add_box(f"sleeve_{group}", (0.085, 0.05, 0.05), DARK, HIDDEN)
            terminal = self.add_box(f"inner_housing_{group}", (0.10, 0.08, 0.07), WHITE, HIDDEN)
            self.wires.append((pieces, sleeve, terminal))
        self.camera = self.scene.add(pyrender.OrthographicCamera(xmag=5.8, ymag=3.25, znear=0.01, zfar=80))
        for eye, intensity in (((-4, -5, 9), 1.8), ((5, 3, 7), 0.7)):
            self.scene.add(
                pyrender.DirectionalLight(color=np.ones(3), intensity=intensity), pose=look_at(eye, (0, 0, 0))
            )

    def node(self, name, mesh):
        node = self.scene.add(mesh, pose=transform(HIDDEN))
        self.names.append(name)
        self.dynamic.append(node)
        return node

    def add_box(self, name, dims, mat, pos, dynamic=True):
        mesh = box_mesh(dims, mat)
        if dynamic:
            node = self.node(name, mesh)
            self.scene.set_pose(node, transform(pos))
            return node
        self.static.append(self.scene.add(mesh, pose=transform(pos)))
        return None

    def add_cylinder(self, name, radius, height, mat, pos):
        node = self.node(name, cylinder_mesh(radius, height, mat, sections=20))
        self.scene.set_pose(node, transform(pos))
        return node

    def set(self, node, pos, rpy=(0, 0, 0)):
        self.scene.set_pose(node, transform(pos, rpy))

    def build_environment(self):
        self.add_box("floor", (16, 8, 0.05), WHITE, (-1.8, 0.3, -0.05), False)
        for x in (-1.55, 1.55):
            self.table(x, 0.8, 1.45, 0.9)
        for x in (-2.85, 2.85):
            self.table(x, 0.3, 0.8, 0.65)
        self.table(0, 0.36, 1.36, 0.98)
        self.table(-6.05, 1.05, 3.65, 3.02)
        self.table(4.0, -0.1, 1.1, 0.8)
        for z in (0.73,):
            for y in (-1.54, -0.86):
                self.add_box("rail", (8.8, 0.09, 0.10), SILVER, (0, y, z), False)
            for x in np.linspace(-4.25, 4.25, 34):
                mesh = cylinder_mesh(0.037, 0.60, SILVER, sections=12)
                self.static.append(self.scene.add(mesh, pose=transform((x, -1.2, z + 0.0055), (math.pi / 2, 0, 0))))
        for x in (-4.3, -2.3, 0, 2.3, 4.3):
            for y in (-1.54, -0.86):
                self.add_box("conveyor_leg", (0.07, 0.07, 0.70), DARK, (x, y, 0.35), False)
        for xmin, xmax, ymin, ymax in ((-8.05, -3.05, -1.8, 2.9), (2.55, 4.25, -1.6, 0.7)):
            for x in (xmin, xmax):
                for y in (ymin, ymax):
                    self.add_box("xyz_post", (0.065, 0.065, 1.65), SILVER, (x, y, 1.16), False)
                self.add_box("xyz_rail", (0.085, ymax - ymin, 0.10), SILVER, (x, (ymin + ymax) / 2, 2), False)
        for x in (-1.55, 1.55, 0):
            self.add_box("tool_support", (0.055, 0.055, 1.6), SILVER, (x + 0.42, 1.05, 0.8), False)
            self.add_box("tool_mount", (0.58, 0.065, 0.065), SILVER, (x + 0.15, 1.05, 1.58), False)

    def table(self, x, y, width, depth):
        self.add_box("table_top", (width, depth, 0.06), WHITE, (x, y, 0.82), False)
        for dx in (-width * 0.40, width * 0.40):
            for dy in (-depth * 0.37, depth * 0.37):
                self.add_box("table_leg", (0.06, 0.06, 0.80), SILVER, (x + dx, y + dy, 0.40), False)

    def build_case(self, name):
        parts = []
        for dims, p in (
            ((0.74, 0.44, 0.025), (0, 0, 0.015)),
            ((0.74, 0.025, 0.27), (0, 0.218, 0.15)),
            ((0.74, 0.025, 0.035), (0, -0.218, 0.025)),
            ((0.075, 0.025, 0.27), (-0.33, -0.218, 0.15)),
            ((0.075, 0.025, 0.27), (0.33, -0.218, 0.15)),
            ((0.075, 0.025, 0.27), (0.075, -0.218, 0.15)),
            ((0.025, 0.42, 0.27), (-0.368, 0, 0.15)),
            ((0.025, 0.42, 0.27), (0.368, 0, 0.15)),
        ):
            parts.append((self.add_box(name, dims, DARK, HIDDEN), np.array(p)))
        return parts

    def build_unit(self, name, panel):
        parts = []

        def part(dims, p, mat):
            parts.append((self.add_box(name, dims, mat, HIDDEN), np.array(p)))

        if panel:
            part((0.56, 0.045, 0.24), (0, 0, 0.13), GREEN)
            for x in (-0.19, 0, 0.19):
                part((0.12, 0.12, 0.065), (x, -0.08, 0.17), WHITE)
                part((0.09, 0.035, 0.025), (x, -0.151, 0.17), SILVER)
        else:
            part((0.61, 0.32, 0.025), (0, 0, 0.015), SILVER)
            parts.append((self.add_cylinder(name, 0.077, 0.12, DARK, HIDDEN), np.array([-0.12, -0.045, 0.085])))
            part((0.09, 0.12, 0.11), (0.14, -0.03, 0.08), DARK)
            part((0.43, 0.045, 0.025), (0, -0.08, 0.15), SILVER)
        return parts

    def build_header(self):
        parts = [(self.add_box("header_flange", (0.27, 0.035, 0.13), ORANGE, HIDDEN), np.array([0, 0, 0]))]
        for x in (-0.09, 0, 0.09):
            parts.extend(
                (
                    (self.add_box("header_port", (0.065, 0.09, 0.09), ORANGE, HIDDEN), np.array([x, -0.052, 0])),
                    (self.add_box("header_opening", (0.043, 0.006, 0.06), DARK, HIDDEN), np.array([x, -0.10, 0])),
                )
            )
        return parts

    def group(self, parts, origin):
        for node, offset in parts:
            self.set(node, np.asarray(origin) + offset)

    def build_hand(self, name):
        return [
            self.add_box(f"{name}_palm", (0.18, 0.13, 0.11), DARK, HIDDEN),
            self.add_box(f"{name}_left_finger", (0.032, 0.10, 0.15), CYAN, HIDDEN),
            self.add_box(f"{name}_right_finger", (0.032, 0.10, 0.15), CYAN, HIDDEN),
            self.add_box(f"{name}_carrier", (1, 0.065, 0.035), DARK, HIDDEN),
        ]

    def hand(self, hand, p, gap):
        p = np.asarray(p)
        self.set(hand[0], p + [0, 0, 0.18])
        self.set(hand[1], p + [-gap / 2 - 0.016, 0, 0.055])
        self.set(hand[2], p + [gap / 2 + 0.016, 0, 0.055])
        carrier = transform(p + [0, 0, 0.14])
        carrier[0, 0] = gap + 0.10
        self.scene.set_pose(hand[3], carrier)

    def build_arm(self, name, base, elbow_side):
        base = np.array(base, dtype=float)
        self.add_box("arm_base", (0.33, 0.33, 0.09), DARK, base + [0, 0, 0.045], False)
        self.static.append(
            self.scene.add(cylinder_mesh(0.11, 0.94, SILVER, sections=20), pose=transform(base + [0, 0, 0.53]))
        )
        links = [self.node(f"{name}_link_{i}", self.unit_cylinder) for i in range(3)]
        joints = [self.node(f"{name}_joint_{i}", self.joint_mesh) for i in range(3)]
        return {"base": base, "side": elbow_side, "links": links, "joints": joints, "hand": self.build_hand(name)}

    def arm(self, name, target, gap):
        arm = self.arms[name]
        shoulder = arm["base"] + [0, 0, 1.02]
        wrist = np.asarray(target) + [0, 0, 0.27]
        delta = wrist - shoulder
        # Constant-length generic display links; no manufacturer model is selected.
        length = 2.0 if name == "AB補助" else 1.65 if name.startswith("C") else 1.4
        distance = np.linalg.norm(delta)
        assert distance < 2 * length, (name, distance)
        direction = delta / distance
        outward = np.array([-direction[1], direction[0], 0]) * arm["side"]
        normal = np.array([0.0, 0.0, 1.0]) + outward * 0.32
        normal -= direction * np.dot(direction, normal)
        normal /= np.linalg.norm(normal)
        elbow = (shoulder + wrist) / 2 + normal * math.sqrt(length * length - (distance / 2) ** 2)
        points = (shoulder, elbow, wrist, np.asarray(target) + [0, 0, 0.21])
        for node, a, b, radius in zip(arm["links"], points, points[1:], (0.072, 0.062, 0.049)):
            pose = cylinder_between_pose(a, b)
            pose[:3, :2] *= radius
            self.scene.set_pose(node, pose)
        for node, p in zip(arm["joints"], points[:3]):
            self.set(node, p)
        self.hand(arm["hand"], target, gap)

    def cable(self, group, start, end, arch=0.13):
        pieces, sleeve, terminal = self.wires[group]
        start, end = np.asarray(start), np.asarray(end)
        points = []
        for u in np.linspace(0, 1, len(pieces) + 1):
            p = start * (1 - u) + end * u
            p[2] += math.sin(math.pi * u) * arch
            points.append(p)
        for node, a, b in zip(pieces, points, points[1:]):
            pose = cylinder_between_pose(a, b)
            pose[:3, :2] *= 0.018
            self.scene.set_pose(node, pose)
        self.set(sleeve, end)
        self.set(terminal, end + [0, -0.055, 0])

    def tool(self, name, p, extension):
        body, bit = self.tools[name]
        self.set(body, np.asarray(p) + [0, 0, 0.68 - extension])
        self.set(bit, np.asarray(p) + [0, 0, 0.40 - extension])

    def animate(self, t):
        a = sample(
            t,
            [
                (0, (-1.55, 0.82, 0.87)),
                (22, (-1.55, 0.82, 0.87)),
                (23.5, (-1.55, 0.82, 1.20)),
                (26, (-0.13, 0.36, 1.20)),
                (27, (-0.13, 0.36, 0.88)),
                (40, (-0.13, 0.36, 0.88)),
                (42, (-0.13, 0.36, 1.48)),
                (44.5, (0, -1.2, 1.48)),
                (47, (0, -1.2, 0.87)),
                (62, (0, -1.2, 0.87)),
                (65, (2.70, -1.2, 0.87)),
                (70, (2.70, -1.2, 0.87)),
                (71.5, (2.70, -1.2, 1.39)),
                (73, (4, -0.1, 1.39)),
                (74, (4, -0.1, 0.87)),
            ],
        )
        b = sample(
            t,
            [
                (0, (2.15, 0.3, 0.87)),
                (12, (2.15, 0.3, 0.87)),
                (13.5, (2.15, 0.3, 1.27)),
                (15.5, (1.55, 0.82, 1.27)),
                (17, (1.55, 0.82, 0.87)),
                (29, (1.55, 0.82, 0.87)),
                (30.5, (1.55, 0.82, 1.35)),
                (33, (-0.13, 0.47, 1.35)),
                (34.5, (-0.13, 0.47, 0.89)),
            ],
        )
        if t >= 40:
            b = a + [0, 0.11, 0.01]

        pallet = sample(
            t,
            [
                (0, (-3.7, -1.2, 0.80)),
                (9.2, (-3.7, -1.2, 0.80)),
                (11, (0, -1.2, 0.80)),
                (62, (0, -1.2, 0.80)),
                (65, (2.70, -1.2, 0.80)),
                (69, (2.70, -1.2, 0.80)),
                (73, (-3.7, -1.2, 0.80)),
            ],
        )
        self.set(self.pallet, pallet)
        case = sample(
            t,
            [
                (0, (-4.7, -0.15, 0.855)),
                (4.6, (-4.7, -0.15, 0.855)),
                (5.6, (-4.7, -0.15, 1.28)),
                (7.7, (-3.7, -1.2, 1.28)),
                (8.7, (-3.7, -1.2, 0.84)),
                (9.2, (-3.7, -1.2, 0.84)),
                (11, (0, -1.2, 0.84)),
                (62, (0, -1.2, 0.84)),
                (65, (2.70, -1.2, 0.84)),
                (69, (2.70, -1.2, 0.84)),
                (73, (-3.7, -1.2, 0.84)),
                (74.7, (-3.7, -1.2, 0.84)),
                (75.9, (-3.7, -1.2, 1.40)),
                (78.2, (-4.7, -0.15, 1.40)),
                (79.4, (-4.7, -0.15, 0.855)),
            ],
        )
        self.group(self.case, case)
        self.group(self.stock_cases[0], HIDDEN)
        if t >= 62:
            a = case + [0, 0, 0.03]
            b = a + [0, 0.11, 0.01]
        self.group(self.a_unit, a)
        self.group(self.b_unit, b)

        home_a, home_b = np.array([-1.65, 1.1, 1.5]), np.array([1.65, 1.1, 1.5])
        a_target = sample(
            t,
            [
                (0, home_a),
                (11, home_a),
                (11.7, (-2.08, 0.37, 0.98)),
                (12.5, (-2.08, 0.37, 0.98)),
                (13.5, (-2.08, 0.37, 1.37)),
                (15, (-1.70, 0.77, 1.37)),
                (16, (-1.70, 0.77, 0.99)),
                (19.5, (-1.70, 0.77, 0.99)),
                (20.5, home_a),
                (21.5, a + [-0.27, 0, 0.05]),
            ],
        )
        a_gap = float(
            sample(t, [(0, 0.24), (11.7, 0.24), (12.2, 0.15), (19, 0.15), (19.7, 0.24), (21.5, 0.15), (22, 0.075)])
        )
        if 21.5 <= t <= 27.7:
            a_target = a + [-0.27, 0, 0.05]
        if t >= 27.7:
            a_gap = float(sample(t, [(27.7, 0.075), (28.2, 0.24)]))
            a_target = sample(
                t,
                [
                    (27.7, a + [-0.27, 0, 0.05]),
                    (29, home_a),
                    (31, (-2.85, 0.3, 1.04)),
                    (32, (-2.85, 0.3, 1.04)),
                    (33.5, (-2.85, 0.3, 1.35)),
                    (35.5, (-1.55, 0.82, 1.35)),
                    (37, (-1.55, 0.82, 0.94)),
                    (43, (-1.55, 0.82, 0.94)),
                    (44, home_a),
                ],
            )
            if 31.5 <= t < 43:
                a_gap = 0.085
        self.arm("A", a_target, a_gap)
        a_part = sample(
            t,
            [
                (0, (-2.08, 0.37, 0.98)),
                (12.2, (-2.08, 0.37, 0.98)),
                (13.5, (-2.08, 0.37, 1.37)),
                (15, (-1.70, 0.77, 1.37)),
                (16, (-1.70, 0.77, 0.99)),
            ],
        )
        if t > 21:
            a_part = a + [-0.15, -0.05, 0.12]
        self.set(self.part_a, a_part)
        a_next = sample(
            t,
            [
                (0, (-2.85, 0.3, 0.89)),
                (32, (-2.85, 0.3, 0.89)),
                (33.5, (-2.85, 0.3, 1.20)),
                (35.5, (-1.55, 0.82, 1.20)),
                (37, (-1.55, 0.82, 0.89)),
            ],
        )
        self.group(self.a_next, a_next)

        b_target = sample(t, [(0, home_b), (10.8, home_b), (11.7, b + [0.20, 0, 0.20])])
        if 11.7 <= t <= 34.5:
            b_target = b + [0.20, 0, 0.20]
        if t > 34.5:
            b_target = sample(
                t,
                [
                    (34.5, b + [0.20, 0, 0.20]),
                    (36, home_b),
                    (37, (2.85, 0.3, 1.08)),
                    (38, (2.85, 0.3, 1.08)),
                    (39, (2.85, 0.3, 1.35)),
                    (41, (1.55, 0.82, 1.35)),
                    (42, (1.55, 0.82, 1.08)),
                    (47, (1.55, 0.82, 1.08)),
                    (48, home_b),
                ],
            )
        b_gap = float(
            sample(
                t,
                [
                    (0, 0.20),
                    (11.7, 0.20),
                    (12, 0.055),
                    (34.4, 0.055),
                    (35, 0.20),
                    (37.5, 0.20),
                    (38, 0.055),
                    (47, 0.055),
                    (48, 0.20),
                ],
            )
        )
        self.arm("B", b_target, b_gap)
        b_next = sample(
            t,
            [
                (0, (2.85, 0.3, 0.88)),
                (38, (2.85, 0.3, 0.88)),
                (39, (2.85, 0.3, 1.15)),
                (41, (1.55, 0.82, 1.15)),
                (42, (1.55, 0.82, 0.88)),
            ],
        )
        self.group(self.b_next, b_next)

        end_a = a + [-0.10, -0.29, 0.24]
        end_b = b + [0.12, -0.22, 0.25]
        if t >= 48:
            end_a = sample(
                t,
                [
                    (48, end_a),
                    (50, (-0.16, -1.25, 1.06)),
                    (55, (-0.16, -1.25, 1.06)),
                    (57, (0.10, -1.48, 1.14)),
                    (61, (0.10, -1.48, 1.14)),
                    (62, (-0.12, -1.24, 1.04)),
                ],
            )
            end_b = sample(t, [(48, end_b), (54, (0.22, -1.22, 1.14)), (59, (0.15, -1.13, 1.06))])
        if t >= 62:
            end_a = case + [-0.12, -0.04, 0.20]
            end_b = case + [0.15, 0.07, 0.22]
        self.cable(0, a + [-0.15, 0, 0.13], end_a, 0.035 if t >= 62 else 0.13)
        self.cable(1, b + [0.12, -0.08, 0.15], end_b, 0.035 if t >= 62 else 0.13)

        assist_home = np.array([0, 1.75, 1.8])
        assist = sample(t, [(0, assist_home), (17, assist_home), (18.3, end_a)])
        if 18.3 <= t < 28:
            assist = end_a
        elif 28 <= t < 29.8:
            assist = sample(t, [(28, end_a), (28.7, end_a + [0, 0, 0.40]), (29.8, end_b)])
        elif 29.8 <= t < 61:
            assist = end_b
        elif t >= 61:
            assist = sample(t, [(61, end_b), (62, end_b + [0, 0, 0.50]), (65, assist_home)])
        assist_gap = float(
            sample(
                t,
                [
                    (0, 0.20),
                    (18.3, 0.20),
                    (18.8, 0.085),
                    (27.7, 0.085),
                    (28, 0.20),
                    (29.8, 0.20),
                    (30.2, 0.085),
                    (60.5, 0.085),
                    (61, 0.20),
                ],
            )
        )
        self.arm("AB補助", assist, assist_gap)

        c_home = np.array([-0.80, -1.90, 1.62])
        caux_home = np.array([0.75, -1.80, 1.60])
        caux = sample(t, [(0, caux_home), (25.5, caux_home), (27.3, end_a + [0, -0.10, 0])])
        if 27.3 <= t < 28:
            caux = end_a + [0, -0.10, 0]
        elif 28 <= t < 61:
            caux = end_a
        elif t >= 61:
            caux = sample(t, [(61, end_a), (62, end_a + [0, 0, 0.5]), (65, caux_home)])
        cg = float(sample(t, [(0, 0.20), (27.3, 0.20), (27.7, 0.085), (60.5, 0.085), (61, 0.20)]))
        self.arm("C補助", caux, cg)

        cmain = sample(t, [(0, c_home), (32, c_home), (33.5, b + [-0.2, 0, 0.20])])
        gap = float(
            sample(t, [(0, 0.20), (33.5, 0.20), (34, 0.055), (38, 0.055), (38.3, 0.20), (39.5, 0.20), (40, 0.07)])
        )
        if 33.5 <= t < 38.3:
            cmain = b + [-0.2, 0, 0.2]
        elif 38.3 <= t < 40:
            cmain = sample(
                t, [(38.3, b + [-0.2, 0, 0.2]), (38.9, a + [-0.27, -0.08, 0.48]), (39.5, a + [-0.27, -0.08, 0.06])]
            )
        elif 40 <= t < 48:
            cmain = a + [-0.27, -0.08, 0.06]
        elif t >= 48:
            cmain = sample(
                t,
                [
                    (48, a + [-0.27, -0.08, 0.06]),
                    (48.7, c_home),
                    (49.5, (-0.82, -0.32, 1.00)),
                    (50, (-0.82, -0.32, 1.00)),
                    (50.6, (-0.82, -0.32, 1.36)),
                    (51.8, (-0.17, -1.50, 1.02)),
                    (54, (-0.17, -1.50, 1.02)),
                    (55, c_home),
                    (55.8, (-0.82, -0.4, 1.0)),
                    (56.3, (-0.82, -0.4, 1.0)),
                    (57, (-0.82, -0.4, 1.35)),
                    (58, (-0.1, -1.2, 1.10)),
                    (60.5, (-0.1, -1.2, 1.10)),
                    (62, c_home),
                ],
            )
            gap = float(
                sample(
                    t,
                    [
                        (48, 0.07),
                        (48.4, 0.35),
                        (49.5, 0.35),
                        (50, 0.285),
                        (54, 0.285),
                        (54.5, 0.35),
                        (55.8, 0.22),
                        (56.3, 0.08),
                        (60.5, 0.08),
                        (61, 0.22),
                    ],
                )
            )
        self.arm("C主", cmain, gap)

        header = sample(
            t,
            [
                (0, (-0.82, -0.32, 1.0)),
                (50, (-0.82, -0.32, 1.0)),
                (50.6, (-0.82, -0.32, 1.36)),
                (51.8, (-0.17, -1.44, 1.01)),
            ],
        )
        if t >= 62:
            header = case + [-0.17, -0.24, 0.17]
        self.group(self.header, header)
        bar = sample(
            t, [(0, (-0.82, -0.4, 1)), (56.3, (-0.82, -0.4, 1)), (57, (-0.82, -0.4, 1.35)), (58, (-0.1, -1.2, 1.10))]
        )
        if t >= 62:
            bar = case + [-0.1, 0, 0.26]
        self.set(self.busbar, bar)

        xyz_pos = sample(
            t,
            [
                (0, (-4.7, -0.15, 1.7)),
                (4, (-4.7, -0.15, 1.7)),
                (4.6, (-4.7, -0.15, 1.01)),
                (5.6, (-4.7, -0.15, 1.42)),
                (7.7, (-3.7, -1.2, 1.42)),
                (8.7, (-3.7, -1.2, 0.98)),
                (9.2, (-3.7, -1.2, 0.98)),
                (10, (-3.7, -1.2, 1.65)),
                (73, (-3.7, -1.2, 1.65)),
                (74.2, (-3.7, -1.2, 0.98)),
                (74.7, (-3.7, -1.2, 0.98)),
                (75.9, (-3.7, -1.2, 1.54)),
                (78.2, (-4.7, -0.15, 1.54)),
                (79.4, (-4.7, -0.15, 0.995)),
                (80.0, (-4.7, -0.15, 0.995)),
                (81.5, (-4.7, -0.15, 1.8)),
            ],
        )
        xyz_gap = float(
            sample(
                t,
                [
                    (0, 0.95),
                    (4.2, 0.95),
                    (4.6, 0.75),
                    (8.7, 0.75),
                    (9.2, 0.95),
                    (74.2, 0.95),
                    (74.7, 0.75),
                    (79.4, 0.75),
                    (80, 0.95),
                ],
            )
        )
        self.hand(self.xyz_hand, xyz_pos, xyz_gap)
        self.set(self.xyz[0], [xyz_pos[0], xyz_pos[1], 2.05])
        self.set(self.xyz[1], [xyz_pos[0], xyz_pos[1], xyz_pos[2] + 0.61])
        self.set(self.xyz[2], [-5.55, xyz_pos[1], 2.03])

        out_p = sample(
            t,
            [
                (0, (3.85, -0.1, 1.8)),
                (65, (3.85, -0.1, 1.8)),
                (65.8, (3.85, -0.1, 0.90)),
                (66.5, (3.85, -0.1, 1.55)),
                (67.4, (2.7, -1.2, 1.55)),
                (68, (2.7, -1.2, 1.14)),
                (68.3, (2.7, -1.2, 1.14)),
                (69, (2.7, -1.2, 1.8)),
                (70, (3.85, -0.1, 1.8)),
            ],
        )
        out_gap = float(sample(t, [(0, 0.95), (65.5, 0.95), (65.8, 0.74), (68, 0.74), (68.3, 0.95)]))
        self.hand(self.out_hand, out_p, out_gap)
        self.set(self.out_xyz[0], [out_p[0], out_p[1], 2.12])
        self.set(self.out_xyz[1], [out_p[0], out_p[1], out_p[2] + 0.61])
        self.set(self.out_xyz[2], [3.4, out_p[1], 2.10])
        lid_pos = sample(
            t,
            [
                (0, (3.85, -0.1, 0.90)),
                (65.8, (3.85, -0.1, 0.90)),
                (66.5, (3.85, -0.1, 1.55)),
                (67.4, (2.7, -1.2, 1.55)),
                (68, (2.7, -1.2, 1.14)),
            ],
        )
        if t >= 69:
            lid_pos = case + [0, 0, 0.30]
        self.set(self.lid, lid_pos)
        self.set(
            self.probe,
            sample(
                t, [(0, (2.7, -1.2, 1.65)), (64, (2.7, -1.2, 1.65)), (65, (2.7, -1.2, 1.27)), (66, (2.7, -1.2, 1.65))]
            ),
        )
        for name, center, times in (
            ("A", (-1.55, 0.82, 1.05), (17, 18, 19, 20)),
            ("B", (1.55, 0.82, 1.13), (18, 19, 20, 21)),
        ):
            extension = float(sample(t, [(0, 0), (times[0], 0), (times[1], 0.25), (times[2], 0.25), (times[3], 0)]))
            if t > 38:
                start = 40 if name == "A" else 44
                extension = float(sample(t, [(start, 0), (start + 1, 0.25), (start + 2, 0.25), (start + 3, 0)]))
            self.tool(name, center, extension)
        c_tool_p = sample(
            t,
            [
                (0, (-0.13, 0.45, 1.14)),
                (40, (-0.13, 0.45, 1.14)),
                (50, (-0.17, -1.40, 1.12)),
                (55, (-0.17, -1.40, 1.12)),
                (57, (-0.27, -1.16, 1.08)),
            ],
        )
        c_ext = float(
            sample(
                t,
                [
                    (0, 0),
                    (35, 0),
                    (36, 0.25),
                    (37.4, 0.25),
                    (38, 0),
                    (52, 0),
                    (52.6, 0.25),
                    (53.3, 0.25),
                    (54, 0),
                    (58.5, 0),
                    (59, 0.25),
                    (60, 0.25),
                    (60.5, 0),
                ],
            )
        )
        self.tool("C", c_tool_p, c_ext)
        if 48 <= t <= 57:
            # A positioning/rotation placeholder, not a selected tool unit.
            body_pos = sample(
                t,
                [
                    (48, (-0.17, -1.12, 1.80)),
                    (50, (-0.17, -2.16, 1.02)),
                    (52, (-0.17, -2.16, 1.02)),
                    (52.6, (-0.17, -1.91, 1.02)),
                    (53.3, (-0.17, -1.91, 1.02)),
                    (54, (-0.17, -2.16, 1.02)),
                    (55, (-0.17, -2.16, 1.02)),
                    (57, (-0.27, -1.16, 1.76)),
                ],
            )
            rotation = float(sample(t, [(48, 0), (50, math.pi / 2), (55, math.pi / 2), (57, 0)]))
            bit_pos = body_pos + np.array([0, math.sin(rotation) * 0.28, -math.cos(rotation) * 0.28])
            self.set(self.tools["C"][0], body_pos, (rotation, 0, 0))
            self.set(self.tools["C"][1], bit_pos, (rotation, 0, 0))

        return self.legacy_camera(t)

    def legacy_camera(self, t):
        if t < 4 or t >= 82:
            eye, target, span = (8, -14, 11), (-1.8, 0.4, 0.7), 7.5
        elif t < 11:
            eye, target, span = (-9, -8, 7), (-5.35, 0.6, 0.9), 3.95
        elif t < 22:
            eye, target, span = (5.5, -6.5, 6), (0, 1.0, 1.0), 3.55
        elif t < 48:
            eye, target, span = (5.2, -7.0, 5.6), (0, -0.2, 1.0), 3.15
        elif t < 62:
            eye, target, span = (2.8, -5.0, 5.8), (-0.05, -1.0, 1.05), 1.65
        elif t < 69:
            eye, target, span = (7.0, -6.0, 5.5), (2.65, -0.7, 0.9), 2.75
        elif t < 74:
            eye, target, span = (6, -13, 9), (-0.6, -0.4, 0.8), 5.9
        else:
            eye, target, span = (-9, -8, 7), (-5.35, 0.6, 0.9), 3.95
        self.scene.set_pose(self.camera, look_at(eye, target))
        self.camera.camera.xmag = span
        self.camera.camera.ymag = span * HEIGHT / WIDTH
        return self.scene.get_pose(self.camera), span
