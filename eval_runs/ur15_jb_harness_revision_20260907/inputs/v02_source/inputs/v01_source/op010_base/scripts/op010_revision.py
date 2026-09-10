#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""OP010 concept-animation geometry and rigid-part targets in SI units."""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pyrender
import trimesh
from probe_op010_grasp import pad_information
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation, Slerp

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "original"))
import render_ur15_line as R  # noqa: E402

R.MESH_ROOT = ROOT / "assets/ur15/visual"
R.ROBOTIQ_MESH_ROOT = ROOT / "assets/robotiq_2f_85_gripper_visualization/meshes/visual"
R.FONT_SANS = str(ROOT / "assets/fonts/NotoSans-Regular.ttf")
R.FONT_MONO = str(ROOT / "assets/fonts/DejaVuSansMono.ttf")
R.FONT_CJK = str(ROOT / "assets/fonts/NotoSansCJK-Bold.ttc")

FINAL_Z = 0.5125
TRAY_Z = -0.002
PORT_Z = 0.012
GRIP_X = 0.100
GRIP_Y = 0.351
GRIP_Z = 0.050
GRIP_WIDTH = 0.030
GRASP_TIME = R.STOCK_GRASP
SEAT_TIME = R.STATION_PHASES[0]["seat"]
RELEASE_TIME = R.STATION_PHASES[0]["release"]
OPEN_END = RELEASE_TIME + 0.65
RETREAT_END = 22.6
FOLD_END = 24.25
STOCK_POINT = R.stock_pick_points(0)[0]
SUPPLY_Z = STOCK_POINT[2] - 0.025


def ease(seconds: float, start: float, end: float) -> float:
    """Return a quintic transition for times [s]."""
    return R.smootherstep((seconds - start) / (end - start))


def box_with_axial_hole(extents: tuple[float, float, float], radius: float, hole_z: float = 0.0) -> trimesh.Trimesh:
    """Build a rectangular body with a through-bore along X; dimensions [m]."""
    depth, width, height = extents
    angles = np.unique(
        np.r_[
            np.linspace(0, 2 * np.pi, 64, endpoint=False),
            [
                np.arctan2(z - hole_z, y) % (2 * np.pi)
                for y in (-width / 2, width / 2)
                for z in (-height / 2, height / 2)
            ],
        ]
    )
    directions = np.column_stack((np.cos(angles), np.sin(angles)))
    outer = []
    for y, z in directions:
        distances = []
        if abs(y) > 1e-12:
            distances.append((np.copysign(width / 2, y)) / y)
        if abs(z) > 1e-12:
            distances.append((np.copysign(height / 2, z) - hole_z) / z)
        distance = min(value for value in distances if value > 0)
        outer.append((distance * y, hole_z + distance * z))
    inner = directions * radius + np.array((0, hole_z))
    outer = np.asarray(outer)
    count = len(angles)
    vertices = []
    for x, ring in ((-depth / 2, outer), (-depth / 2, inner), (depth / 2, outer), (depth / 2, inner)):
        vertices.extend(np.column_stack((np.full(count, x), ring)))
    faces = []
    for index in range(count):
        after = (index + 1) % count
        for a, b, c, d in (
            (index, after, count + after, count + index),
            (2 * count + index, 3 * count + index, 3 * count + after, 2 * count + after),
            (index, 2 * count + index, 2 * count + after, after),
            (count + index, count + after, 3 * count + after, 3 * count + index),
        ):
            faces.extend(((a, b, c), (a, c, d)))
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    mesh.fix_normals()
    return mesh


def housing_mesh() -> pyrender.Mesh:
    """Create the open enclosure with a 545 × 765 mm nominal flange [m]."""
    parts = []
    # The four edge reliefs clear the unchanged pallet corner locators.
    parts.append((R.chamfer_box((0.528, 0.765, 0.016), 0.002), R.transform((0, 0, -0.047)), R.MAT_BRUSHED))
    for sign in (-1, 1):
        for start, end in ((-0.3825, -0.345), (-0.255, 0.255), (0.345, 0.3825)):
            parts.append(
                (
                    R.chamfer_box((0.0085, end - start, 0.016), 0.0005),
                    R.transform((sign * 0.26825, (start + end) / 2, -0.047)),
                    R.MAT_BRUSHED,
                )
            )
    parts.append((R.chamfer_box((0.50, 0.72, 0.020), 0.004), R.transform((0, 0, -0.029)), R.MAT_BRUSHED))
    # Long walls have real openings aligned with the four cable entries.
    for wall_x in (-0.238, 0.238):
        for start, end in ((-0.36, -0.328), (-0.272, 0.272), (0.328, 0.36)):
            parts.append(
                (
                    R.chamfer_box((0.024, end - start, 0.080), 0.0005),
                    R.transform((wall_x, (start + end) / 2, 0.015)),
                    R.MAT_BRUSHED,
                )
            )
        for port_y in (-0.30, 0.30):
            parts.append(
                (
                    box_with_axial_hole((0.024, 0.056, 0.080), 0.017, PORT_Z - 0.015),
                    R.transform((wall_x, port_y, 0.015)),
                    R.MAT_BRUSHED,
                )
            )
    for wall_y in (-0.348, 0.348):
        parts.append((R.chamfer_box((0.452, 0.024, 0.080), 0.002), R.transform((0, wall_y, 0.015)), R.MAT_BRUSHED))
    # The source's solid "sealing rim" is replaced by four open rim rails.
    for x in (-0.241, 0.241):
        parts.append((R.chamfer_box((0.030, 0.732, 0.010), 0.001), R.transform((x, 0, 0.050)), R.MAT_ALUMINUM))
    for y in (-0.351, 0.351):
        parts.append((R.chamfer_box((0.452, 0.030, 0.010), 0.001), R.transform((0, y, 0.050)), R.MAT_ALUMINUM))
    for x in (-0.242, 0.242):
        for y in (-0.352, 0.352):
            parts.extend(
                (
                    (R.chamfer_cylinder(0.024, 0.022, sections=20), R.transform((x, y, -0.044)), R.MAT_BRUSHED),
                    (R.hex_bolt(0.017, 0.010), R.transform((x, y, -0.033)), R.MAT_STEEL),
                )
            )
    for y in np.linspace(-0.24, 0.24, 7):
        for x in (-0.252, 0.252):
            parts.append((R.chamfer_box((0.012, 0.026, 0.064), 0.003), R.transform((x, y, 0.012)), R.MAT_BRUSHED))
    return R.assembly_mesh(parts)


def cable_entry_mesh() -> pyrender.Mesh:
    """Create a low-profile flanged through-sleeve; dimensions [m]."""
    parts = [(box_with_axial_hole((0.006, 0.086, 0.072), 0.017), R.transform((0.015, 0, 0)), R.MAT_BLACK)]
    parts.append(
        (
            trimesh.creation.annulus(r_min=0.015, r_max=0.017, height=0.041, sections=40),
            R.transform((0.0055, 0, 0), rpy=(0, np.pi / 2, 0)),
            R.MAT_BLACK,
        )
    )
    parts.append(
        (
            trimesh.creation.annulus(r_min=0.017, r_max=0.026, height=0.010, sections=6),
            R.transform((0.024, 0, 0), rpy=(0, np.pi / 2, 0)),
            R.MAT_DARK_METAL,
        )
    )
    for y in (-0.032, 0.032):
        parts.append((R.hex_bolt(0.008, 0.004), R.transform((0.018, y, 0), rpy=(0, np.pi / 2, 0)), R.MAT_STEEL))
    return R.assembly_mesh(parts)


def component_specs() -> list[tuple[str, pyrender.Mesh, np.ndarray]]:
    """Return the draft preassembled supply set with local transforms [m]."""
    specs = [("housing", housing_mesh(), np.eye(4)), ("tray", R.busbar_tray_mesh(), R.transform((0, 0, TRAY_Z)))]
    entry = cable_entry_mesh()
    for x in (-0.238, 0.238):
        for y in (-0.30, 0.30):
            specs.append(
                (f"cable_entry_{len(specs) - 1}", entry, R.transform((x, y, PORT_Z), rpy=(0, np.pi if x < 0 else 0, 0)))
            )
    return specs


def housing_pose(seconds: float) -> np.ndarray:
    """Return the housing's rigid world pose for the draft transfer [m]."""
    stock_x, _, _ = STOCK_POINT
    stock_z = SUPPLY_Z
    if seconds <= GRASP_TIME:
        return R.transform((stock_x, -4.0, stock_z), rpy=(0, np.pi / 2, 0))
    if seconds < 8.8:
        pull = ease(seconds, GRASP_TIME, 7.8)
        carry = ease(seconds, 7.8, 8.8)
        x = stock_x + 0.16 * pull
        x += (-1.68 - x) * carry
        z = stock_z + 0.17 * pull
        z += (1.11 - z) * carry
        return R.transform((x, -4.0, z), rpy=(0, np.pi / 2, 0))
    if seconds < 12.2:
        root = R.cell_rotation_root(0, seconds)
        front = root[:3, :3] @ np.array((0, -0.78, 0))
        rotation = (
            root[:3, :3]
            @ Rotation.from_euler("z", np.pi / 2).as_matrix()
            @ Rotation.from_euler("y", np.pi / 2).as_matrix()
        )
        pose = R.transform((root[0, 3] + front[0], root[1, 3] + front[1], 1.11))
        pose[:3, :3] = rotation
        return pose
    lay = ease(seconds, 12.2, R.WORK_START)
    x = -0.12 * (1 - lay)
    z = 1.11 + (0.86 - 1.11) * lay
    z += (0.55 - z) * ease(seconds, R.WORK_START, 18.8)
    final = FINAL_Z + R.clamp_lift(seconds)
    z += (final - z) * ease(seconds, 18.8, SEAT_TIME)
    pose = R.transform((x, -4.0, z))
    pose[:3, :3] = (
        Rotation.from_euler("z", np.pi).as_matrix() @ Rotation.from_euler("y", (1 - lay) * np.pi / 2).as_matrix()
    )
    return pose


@lru_cache(maxsize=2048)
def target(seconds: float, side: str) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    """Return desired tool pose [m], normalized grip, seed [rad], base [m]."""
    source_joints, _ = R.motion_at(seconds, side, 0)
    base = R.cell_root(0, seconds) @ R.yoke_base_pose(side)
    _, original_tool = R.UR15.forward(base, source_joints)
    if seconds <= 3.2 or seconds >= FOLD_END:
        return original_tool, 0.0, source_joints, base
    closed = brentq(lambda a: pad_information(a)[0] - GRIP_WIDTH, 0.0, 0.8)
    opened = brentq(lambda a: pad_information(a)[0] - 0.070, 0.0, 0.8)
    close = ease(seconds, 6.0, GRASP_TIME)
    opening = ease(seconds, RELEASE_TIME, OPEN_END)
    angle = opened + (closed - opened) * close * (1 - opening)
    _, pad_center = pad_information(angle)
    pose = housing_pose(seconds)
    lean = np.radians(-10 + 40 * ease(seconds, 12.2, R.WORK_START))
    rotation = pose[:3, :3] @ Rotation.from_euler("y", lean).as_matrix() @ Rotation.from_euler("x", np.pi).as_matrix()
    sign = 1 if side == "left" else -1
    center = np.array((GRIP_X, sign * GRIP_Y, GRIP_Z))
    center[2] += 0.090 * (1 - ease(seconds, 5.4, 6.0))
    center[2] += 0.20 * ease(seconds, OPEN_END, RETREAT_END)
    desired = pose.copy()
    desired[:3, :3] = rotation
    desired[:3, 3] = (pose @ np.r_[center, 1])[:3] - rotation @ pad_center
    weight = ease(seconds, 3.2, 5.4) * (1 - ease(seconds, RETREAT_END, FOLD_END))
    if weight < 1:
        desired[:3, 3] = original_tool[:3, 3] * (1 - weight) + desired[:3, 3] * weight
        desired[:3, :3] = Slerp([0, 1], Rotation.from_matrix(np.array([original_tool[:3, :3], desired[:3, :3]])))(
            weight
        ).as_matrix()
    return desired, angle / 0.8 * weight, source_joints, base


def generate_motion() -> None:
    """Solve and record source-FK trajectories, rejecting errors [m, rad]."""
    frames = round(R.DURATION * 30)
    joints_all = np.empty((frames, 2, 6))
    grips = np.empty((frames, 2))
    housing = np.array([housing_pose(frame / 30) for frame in range(frames)])
    errors = []
    previous = {}
    failed = []
    for frame in range(frames):
        seconds = frame / 30
        for index, side in enumerate(("left", "right")):
            desired, grip, original, base = target(seconds, side)
            seeds = [previous.get(side, original), original]
            for bend in (-1.2, 1.2):
                seed = original.copy()
                seed[2] = bend
                seeds.append(seed)
            best = None
            for seed in seeds:
                joints, residual = R.solve_tool_pose(base, desired[:3, 3], seed, orientation=desired[:3, :3])
                if best is None or residual < best[1]:
                    best = (joints, residual)
                if residual < 1e-6:
                    break
            joints, residual = best
            if side in previous:
                joints += np.round((previous[side] - joints) / (2 * np.pi)) * (2 * np.pi)
            _, actual = R.UR15.forward(base, joints)
            pos_error = float(np.linalg.norm(actual[:3, 3] - desired[:3, 3]))
            rot_error = float(np.linalg.norm(Rotation.from_matrix(actual[:3, :3] @ desired[:3, :3].T).as_rotvec()))
            errors.append((pos_error, rot_error))
            if pos_error > 1e-5 or rot_error > 1e-5:
                failed.append(
                    {
                        "frame": frame + 1,
                        "seconds": seconds,
                        "side": side,
                        "position_error_m": pos_error,
                        "rotation_error_rad": rot_error,
                    }
                )
            else:
                previous[side] = joints
            joints_all[frame, index] = joints
            grips[frame, index] = grip
        if frame % 120 == 0:
            print("MOTION", frame, "/", frames, "failed", len(failed), flush=True)
    steps = np.abs(np.diff(joints_all, axis=0))
    report = {
        "purpose": "Geometric animation consistency only",
        "frames": frames,
        "fps": 30,
        "max_position_error_m": float(np.max(np.array(errors)[:, 0])),
        "max_rotation_error_rad": float(np.max(np.array(errors)[:, 1])),
        "max_frame_joint_step_rad": float(steps.max()),
        "failed_count": len(failed),
        "failures": failed,
        "phases_s": {
            "grasp": GRASP_TIME,
            "seat": SEAT_TIME,
            "release": RELEASE_TIME,
            "opened": OPEN_END,
            "retreated": RETREAT_END,
        },
        "grip_surface": {
            "kind": "outer_rim",
            "x_m": GRIP_X,
            "y_m": [-GRIP_Y, GRIP_Y],
            "z_m": GRIP_Z,
            "thickness_m": GRIP_WIDTH,
        },
    }
    (ROOT / "audit/motion_checks.json").write_text(json.dumps(report, indent=2) + "\n")
    if failed or steps.max() > 0.20:
        raise RuntimeError(
            f"Trajectory rejected: failed={len(failed)} maximum joint step={steps.max():.6g}; "
            "see audit/motion_checks.json"
        )
    np.savez_compressed(ROOT / "data/op010_motion.npz", joints=joints_all, grips=grips, housing=housing)
    print(json.dumps({key: value for key, value in report.items() if key != "failures"}, indent=2), flush=True)


def install_revision() -> None:
    """Install the OP010 draft into the original scene builder and animator."""
    specs = component_specs()
    solids = []
    for _, mesh, local in specs:
        for primitive in mesh.primitives:
            solids.append(
                (
                    trimesh.Trimesh(
                        vertices=primitive.positions,
                        faces=(
                            primitive.indices
                            if primitive.indices is not None
                            else np.arange(len(primitive.positions)).reshape(-1, 3)
                        ),
                        process=False,
                    ),
                    local,
                    primitive.material,
                )
            )
    supply = R.assembly_mesh(solids)
    source_stocker = R.add_stocker
    source_build = R.build_scene
    source_pose = R.pose_scene
    stock_nodes = []
    motion = np.load(ROOT / "data/op010_motion.npz")
    checks = json.loads((ROOT / "audit/motion_checks.json").read_text())
    if checks["failed_count"] or checks["max_frame_joint_step_rad"] > 0.20:
        raise RuntimeError("Unaccepted geometric trajectory; regenerate before scene export")

    def stocker(scene, cell_index, cx, cy):
        before = set(scene.mesh_nodes)
        result = source_stocker(scene, cell_index, cx, cy)
        if cell_index == 0:
            selected = [node for node in set(scene.mesh_nodes) - before if node.mesh is supply]
            selected.sort(key=lambda node: -scene.get_pose(node)[0, 3])
            if len(selected) != 4:
                raise RuntimeError(f"Expected the original four housing slots, found {len(selected)}")
            for index, node in enumerate(selected):
                pose = scene.get_pose(node).copy()
                pose[2, 3] = SUPPLY_Z
                scene.set_pose(node, pose=pose)
                node.name = f"OP010_supply_slot_{index + 1}"
                stock_nodes.append((node, pose))
        return result

    def build():
        state = source_build()
        for item in state[5]:
            if item.required_stage != 1:
                continue
            if item.node.mesh is supply:
                item.local_pose = R.transform((0, 0, FINAL_Z), rpy=(0, 0, np.pi))
                item.node.name = "housing_preassembled_on_pallet"
            else:
                item.required_stage = 99
                item.node.name = "legacy_component_replaced_by_preassembly"
        return state

    def pose(*state_and_time):
        *state, seconds = state_and_time
        source_pose(*state, seconds)
        scene, actors, _, shared = state[:4]
        frame = int(np.clip(round(seconds * 30), 0, len(motion["joints"]) - 1))
        for actor in actors:
            if actor.cell_index != 0:
                continue
            index = 0 if actor.side == "left" else 1
            actor.robot.base_pose = R.cell_root(0, seconds) @ actor.base_local_pose
            actor.robot.update(motion["joints"][frame, index], motion["grips"][frame, index])
            scene.set_pose(actor.puck_node, pose=R.transform((0, 0, -10)))
            scene.set_pose(actor.collar_node, pose=R.transform((0, 0, -10)))
        carried = next(value for value in shared if value.cell_index == 0)
        scene.set_pose(
            carried.node,
            pose=housing_pose(seconds) if GRASP_TIME <= seconds < RELEASE_TIME else R.transform((0, 0, -10)),
        )
        for index, (node, original) in enumerate(stock_nodes):
            scene.set_pose(node, pose=R.transform((0, 0, -10)) if index == 0 and seconds >= GRASP_TIME else original)

    R.housing_assembly_mesh = lambda: supply
    R.add_stocker = stocker
    R.build_scene = build
    R.pose_scene = pose


if __name__ == "__main__":
    generate_motion()
