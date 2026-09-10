#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Render a cinematic UR15 reinforcement-learning concept video."""

from __future__ import annotations

import argparse
import itertools
import math
import subprocess
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
import pyrender
import trimesh
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

MESH_ROOT = Path("/home/rlrk/src/ur15-line-render/assets/Universal_Robots_ROS2_Description/meshes/ur15/visual")
ROBOTIQ_MESH_ROOT = Path(
    "/home/rlrk/src/ur15-line-render/assets/robotiq/robotiq_2f_85_gripper_visualization/meshes/visual"
)
FONT_SANS = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
WIDTH = 1280
HEIGHT = 720
FPS = 30
DURATION = 26.2667
GRIPPER_OBJECT_OFFSET = 0.19
# Overall illuminance of the bay, applied to every fixture and to the bounce
# term together so the balance between them does not shift.
LIGHT_LEVEL = 0.64
T_FRAME_RADIUS = 0.102
LIFT_TRAVEL = 0.16
T_FRAME_STEM_BOTTOM = 0.37
T_FRAME_STEM_HEIGHT = 0.58 * 2.0
SHOULDER_HEIGHT = T_FRAME_STEM_BOTTOM + T_FRAME_STEM_HEIGHT
SHOULDER_SPAN = 1.04 / 3.0
# The arms are carried on an angled yoke — a Y rather than the flat T they
# were first mounted on. The work poses further down were hand-tuned against
# the flat mounting, so they are retargeted onto this one by inverse
# kinematics instead of being re-tuned.
YOKE_ANGLE = math.radians(45.0)
YOKE_SPREAD = 0.22
YOKE_RISE = 0.0
CELL_X_OFFSET = 0.90
LOWER_BASE_RADIUS = 0.215
ORIGINAL_STOCKER_INNER_X = 1.52
STOCKER_CLEARANCE = 2.0 * (ORIGINAL_STOCKER_INNER_X - CELL_X_OFFSET - LOWER_BASE_RADIUS)
STOCKER_INNER_X = CELL_X_OFFSET + LOWER_BASE_RADIUS + STOCKER_CLEARANCE
STOCKER_OUTER_X = STOCKER_INNER_X + 0.32
CELL_Y_START = -4.00
CELL_Y_SPACING = 1.15

# Indexed (stop-and-clamp) transfer, as on a free-flow pallet line.
# Every pallet advances exactly one station pitch per cycle, is held by the
# station stopper, raised onto locating pins by the lift-and-clamp unit,
# worked by all ten cells during the same dwell, then released. The transfer
# covers 1.15 m in about 3.3 s (~21 m/min), a normal pallet conveyor rate.
# Everything the machines do is played at half speed, so every hand-set
# duration below is stretched by PACE and the cycle stretches with it.
PACE = 4.0
CYCLES = 1
CYCLE_TIME = DURATION / CYCLES
INDEX_TIME = CYCLE_TIME * 0.50
CLAMP_TIME = CYCLE_TIME * 0.055
RELEASE_TIME = CYCLE_TIME * 0.055
WORK_TIME = CYCLE_TIME - INDEX_TIME - CLAMP_TIME - RELEASE_TIME
WORK_START = INDEX_TIME + CLAMP_TIME
WORK_END = CYCLE_TIME - RELEASE_TIME
CLAMP_RISE = 0.014
STOPPER_STROKE = 0.055

# Cell cycle: the table carries the arms away from the line while a pallet
# transfers, picks the next component from the stocker behind it, turns back
# and waits above the station until the pallet is clamped.
TURN_BACK_START = 0.00
TURN_BACK_TIME = 0.80 * PACE
STOCK_REACH = 1.15 * PACE
STOCK_CONTACT = 1.50 * PACE
STOCK_GRASP = 1.72 * PACE
STOCK_CLEAR = 1.95 * PACE
TURN_OUT_START = 2.20 * PACE
TURN_OUT_TIME = 0.85 * PACE
# The arm reaches over the conveyor while the table is still swinging back, so
# it is already holding the next component in the ready pose above the station
# when the pallet clamps, and can start seating it immediately.
TURN_OUT_HOLD = TURN_OUT_START + TURN_OUT_TIME * 0.55
READY_TIME = TURN_OUT_START + TURN_OUT_TIME
SEAT_TIME = WORK_START + WORK_TIME * 0.32
RELEASE_PHASE = WORK_START + WORK_TIME * 0.42

PANEL_PITCH = CELL_Y_SPACING
PANEL_COUNT = 22
CONVEYOR_Y_MAX = 8.00
CONVEYOR_LENGTH = PANEL_COUNT * PANEL_PITCH
CONVEYOR_Y_MIN = CONVEYOR_Y_MAX - CONVEYOR_LENGTH
CONVEYOR_CENTER_Y = (CONVEYOR_Y_MIN + CONVEYOR_Y_MAX) / 2.0
# Offset that puts every pallet exactly on a station pitch while docked.
PANEL_BASE_OFFSET = (CELL_Y_START - CONVEYOR_Y_MIN) % PANEL_PITCH


def transform(xyz=(0.0, 0.0, 0.0), rpy=(0.0, 0.0, 0.0)):
    result = np.eye(4)
    result[:3, :3] = Rotation.from_euler("xyz", rpy).as_matrix()
    result[:3, 3] = xyz
    return result


def rotate_z(angle):
    return transform(rpy=(0.0, 0.0, angle))


def look_at(eye, target, up=(0.0, 0.0, 1.0)):
    eye = np.asarray(eye, dtype=float)
    target = np.asarray(target, dtype=float)
    up = np.asarray(up, dtype=float)
    camera_z = eye - target
    camera_z /= np.linalg.norm(camera_z)
    camera_x = np.cross(up, camera_z)
    camera_x /= np.linalg.norm(camera_x)
    camera_y = np.cross(camera_z, camera_x)
    result = np.eye(4)
    result[:3, :3] = np.column_stack((camera_x, camera_y, camera_z))
    result[:3, 3] = eye
    return result


def material(color, metallic=0.0, roughness=0.7, emissive=None):
    kwargs = {
        "baseColorFactor": color,
        "metallicFactor": metallic,
        "roughnessFactor": roughness,
    }
    if emissive is not None:
        kwargs["emissiveFactor"] = emissive
    return pyrender.MetallicRoughnessMaterial(**kwargs)


MAT_CONCRETE = material((0.52, 0.55, 0.54, 1.0), 0.0, 0.82)
MAT_WALL = material((0.72, 0.75, 0.74, 1.0), 0.08, 0.62)
MAT_FLOOR = material((0.43, 0.47, 0.46, 1.0), 0.16, 0.52)
MAT_WHITE = material((0.78, 0.81, 0.80, 1.0), 0.22, 0.34)
MAT_WHITE_SATIN = material((0.66, 0.70, 0.69, 1.0), 0.32, 0.42)
MAT_ALUMINUM = material((0.58, 0.62, 0.62, 1.0), 0.86, 0.25)
MAT_DARK_METAL = material((0.035, 0.047, 0.047, 1.0), 0.85, 0.27)
MAT_BRUSHED = material((0.38, 0.42, 0.42, 1.0), 0.82, 0.32)
MAT_BLACK = material((0.012, 0.016, 0.016, 1.0), 0.52, 0.42)
MAT_GREEN = material((0.02, 0.24, 0.13, 1.0), 0.15, 0.28, emissive=(0.02, 0.42, 0.21))
MAT_AMBER = material((0.38, 0.15, 0.025, 1.0), 0.1, 0.25, emissive=(1.0, 0.28, 0.02))
MAT_HV_ORANGE = material((0.88, 0.19, 0.025, 1.0), 0.16, 0.34)
MAT_PUCK = material((0.18, 0.53, 0.37, 1.0), 0.28, 0.3)
MAT_PUCK_BLUE = material((0.13, 0.43, 0.58, 1.0), 0.3, 0.26)
MAT_CYAN = material((0.02, 0.20, 0.25, 1.0), 0.12, 0.25, emissive=(0.02, 0.34, 0.48))
MAT_LIGHT = material((0.62, 0.78, 0.72, 1.0), 0.0, 0.18, emissive=(0.74, 1.0, 0.91))
MAT_SCREEN = material((0.005, 0.035, 0.025, 1.0), 0.0, 0.45, emissive=(0.01, 0.19, 0.11))
# Plant equipment finishes: RAL 7035 enclosures, safety yellow, galvanised
# steel structure and the lamp colours of a three-tier status light.
MAT_CABINET = material((0.56, 0.59, 0.58, 1.0), 0.28, 0.44)
MAT_CABINET_TRIM = material((0.20, 0.23, 0.24, 1.0), 0.40, 0.40)
MAT_SAFETY_YELLOW = material((0.80, 0.55, 0.02, 1.0), 0.06, 0.52)
MAT_ESTOP_RED = material((0.62, 0.03, 0.02, 1.0), 0.08, 0.38)
MAT_STEEL = material((0.32, 0.35, 0.36, 1.0), 0.72, 0.40)
MAT_TRUSS = material((0.27, 0.30, 0.31, 1.0), 0.50, 0.55)
MAT_CEILING = material((0.20, 0.22, 0.23, 1.0), 0.04, 0.88)
MAT_DUCT = material((0.44, 0.47, 0.47, 1.0), 0.22, 0.55)
MAT_HOSE = material((0.09, 0.11, 0.12, 1.0), 0.18, 0.62)
MAT_LAMP_OFF = material((0.16, 0.17, 0.17, 1.0), 0.05, 0.42)
MAT_LAMP_GREEN = material((0.04, 0.30, 0.12, 1.0), 0.0, 0.24, emissive=(0.10, 1.0, 0.34))
MAT_LAMP_AMBER = material((0.34, 0.19, 0.02, 1.0), 0.0, 0.24, emissive=(1.0, 0.52, 0.04))
MAT_LENS = material(
    (0.66, 0.72, 0.70, 1.0),
    0.0,
    0.16,
    emissive=(0.50 * LIGHT_LEVEL, 0.60 * LIGHT_LEVEL, 0.56 * LIGHT_LEVEL),
)
MAT_SCANNER = material((0.14, 0.16, 0.17, 1.0), 0.30, 0.40)


def box_mesh(extents, mat):
    return pyrender.Mesh.from_trimesh(trimesh.creation.box(extents=extents), material=mat, smooth=False)


def cylinder_mesh(radius, height, mat, sections=48):
    return pyrender.Mesh.from_trimesh(
        trimesh.creation.cylinder(radius=radius, height=height, sections=sections),
        material=mat,
        smooth=True,
    )


def sphere_mesh(radius, mat):
    return pyrender.Mesh.from_trimesh(
        trimesh.creation.icosphere(subdivisions=2, radius=radius),
        material=mat,
        smooth=True,
    )


def tapered_box(bottom_width, top_width, depth, height):
    bottom = bottom_width / 2.0
    top = top_width / 2.0
    half_depth = depth / 2.0
    half_height = height / 2.0
    vertices = np.array(
        (
            (-bottom, -half_depth, -half_height),
            (bottom, -half_depth, -half_height),
            (bottom, half_depth, -half_height),
            (-bottom, half_depth, -half_height),
            (-top, -half_depth, half_height),
            (top, -half_depth, half_height),
            (top, half_depth, half_height),
            (-top, half_depth, half_height),
        )
    )
    faces = np.array(
        (
            (0, 2, 1),
            (0, 3, 2),
            (4, 5, 6),
            (4, 6, 7),
            (0, 1, 5),
            (0, 5, 4),
            (1, 2, 6),
            (1, 6, 5),
            (2, 3, 7),
            (2, 7, 6),
            (3, 0, 4),
            (3, 4, 7),
        )
    )
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)


def tapered_box_mesh(bottom_width, top_width, depth, height, mat):
    return pyrender.Mesh.from_trimesh(
        tapered_box(bottom_width, top_width, depth, height),
        material=mat,
        smooth=False,
    )


# ---------------------------------------------------------------------------
# Part shapes.
#
# Nothing on a real machine has a sharp arris: sheet metal folds to a radius,
# machined faces get an edge break, mouldings are drafted and filleted. A plain
# box has none of that, and a line built out of plain boxes reads as a drawing
# rather than as equipment — the edges go dead instead of catching a highlight.
# The primitives below carry that edge treatment, and the small hardware that a
# photograph of the same machine would show: bolt heads, levelling feet, the
# slots down an aluminium profile.
# ---------------------------------------------------------------------------


def _hull(points):
    return trimesh.Trimesh(vertices=np.asarray(points, dtype=float)).convex_hull


def chamfer_box(extents, chamfer=None):
    """A box with a flat bevel on every edge: the machined-part default."""
    half = np.asarray(extents, dtype=float) / 2.0
    limit = float(half.min())
    if chamfer is None:
        chamfer = min(0.010, limit * 0.26)
    chamfer = float(np.clip(chamfer, 1e-4, limit * 0.48))
    inner = half - chamfer
    points = []
    for signs in itertools.product((-1.0, 1.0), repeat=3):
        corner = inner * np.asarray(signs)
        for axis in range(3):
            point = corner.copy()
            point[axis] = half[axis] * signs[axis]
            points.append(point)
    return _hull(points)


def fillet_box(extents, radius=None, subdivisions=1):
    """A box with rounded edges, for mouldings, covers and folded skins."""
    half = np.asarray(extents, dtype=float) / 2.0
    limit = float(half.min())
    if radius is None:
        radius = min(0.018, limit * 0.42)
    radius = float(np.clip(radius, 1e-4, limit * 0.98))
    ball = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)
    inner = np.maximum(half - radius, 0.0)
    points = [ball.vertices + inner * np.asarray(signs) for signs in itertools.product((-1.0, 1.0), repeat=3)]
    return _hull(np.vstack(points))


def chamfer_cylinder(radius, height, chamfer=None, sections=32):
    """A turned part with both ends broken."""
    if chamfer is None:
        chamfer = min(0.006, radius * 0.22, height * 0.22)
    chamfer = float(np.clip(chamfer, 1e-5, min(radius, height / 2.0) * 0.9))
    angles = np.linspace(0.0, 2.0 * math.pi, sections, endpoint=False)
    ring = np.column_stack((np.cos(angles), np.sin(angles)))
    rings = []
    for scale, z in (
        (radius - chamfer, -height / 2.0),
        (radius, -height / 2.0 + chamfer),
        (radius, height / 2.0 - chamfer),
        (radius - chamfer, height / 2.0),
    ):
        rings.append(np.column_stack((ring * scale, np.full(sections, z))))
    return _hull(np.vstack(rings))


def hex_bolt(across_flats, height):
    """Hex head on its washer face. Fastener heads are what give a joint scale."""
    head = trimesh.creation.cylinder(radius=across_flats / 1.7320508, height=height, sections=6)
    head.apply_translation((0.0, 0.0, height / 2.0))
    washer = trimesh.creation.cylinder(radius=across_flats * 0.66, height=height * 0.24, sections=20)
    washer.apply_translation((0.0, 0.0, height * 0.12))
    return trimesh.util.concatenate((head, washer))


# Local bounds of the solids inside each merged mesh, keyed by mesh id.
PART_BOUNDS: dict[int, list] = {}


def assembly_mesh(parts):
    """One mesh out of many small solids, grouped by material.

    Detail costs nodes and every node costs a draw call, so a bolt pattern, a
    bank of rollers or a whole stand is merged down to one mesh with one
    primitive per finish — as cheap to draw as the single box it replaces.
    """
    groups: dict[int, tuple] = {}
    bounds = []
    for geometry, pose, mat in parts:
        piece = geometry.copy()
        if pose is not None:
            piece.apply_transform(np.asarray(pose, dtype=float))
        groups.setdefault(id(mat), (mat, []))[1].append(piece)
        bounds.append(piece.bounds.copy())
    primitives = []
    for mat, pieces in groups.values():
        merged = trimesh.util.concatenate(pieces)
        primitives.extend(pyrender.Mesh.from_trimesh(merged, material=mat, smooth=False).primitives)
    mesh = pyrender.Mesh(primitives=primitives)
    # Remember what went into it, so the clash audit can still see the parts
    # once they have been merged into one draw call.
    PART_BOUNDS[id(mesh)] = bounds
    return mesh


def rounded_box_mesh(extents, mat, chamfer=None):
    return pyrender.Mesh.from_trimesh(chamfer_box(extents, chamfer), material=mat, smooth=False)


def soft_box_mesh(extents, mat, radius=None, subdivisions=1):
    return pyrender.Mesh.from_trimesh(fillet_box(extents, radius, subdivisions), material=mat, smooth=False)


def turned_mesh(radius, height, mat, chamfer=None, sections=40):
    return pyrender.Mesh.from_trimesh(
        chamfer_cylinder(radius, height, chamfer, sections),
        material=mat,
        smooth=False,
    )


def extrusion_parts(
    section,
    length,
    pose=None,
    mat=MAT_ALUMINUM,
    core_mat=MAT_DARK_METAL,
    depth_ratio=0.16,
    groove_ratio=0.34,
):
    """A T-slot aluminium profile, built as the slotted section it really is.

    A dark core carries the groove floors and eight chamfered lands stand
    proud of it, so the profile shows the four slots that identify it instead
    of being a bar with a stripe painted down it. Extruded along +Z.
    """
    pose = np.eye(4) if pose is None else np.asarray(pose, dtype=float)
    if np.isscalar(section):
        size_x = size_y = float(section)
    else:
        size_x, size_y = (float(value) for value in section)
    depth = min(size_x, size_y) * depth_ratio
    land_x = (size_x - size_x * groove_ratio) / 2.0
    land_y = (size_y - size_y * groove_ratio) / 2.0
    parts = [
        (
            trimesh.creation.box(extents=(size_x - 2.0 * depth, size_y - 2.0 * depth, length)),
            pose,
            core_mat,
        )
    ]
    chamfer = min(depth * 0.55, land_x * 0.30, land_y * 0.30, 0.006)
    for outward in (-1.0, 1.0):
        for along in (-1.0, 1.0):
            parts.append(
                (
                    chamfer_box((depth, land_y, length), chamfer),
                    pose
                    @ transform(
                        (
                            outward * (size_x - depth) / 2.0,
                            along * (size_y - land_y) / 2.0,
                            0.0,
                        )
                    ),
                    mat,
                )
            )
            parts.append(
                (
                    chamfer_box((land_x, depth, length), chamfer),
                    pose
                    @ transform(
                        (
                            along * (size_x - land_x) / 2.0,
                            outward * (size_y - depth) / 2.0,
                            0.0,
                        )
                    ),
                    mat,
                )
            )
    return parts


def levelling_foot_parts(pose=None, plate=0.11, mat=MAT_DARK_METAL):
    """Foot plate, adjuster and lock nut — how a stand actually meets a floor."""
    pose = np.eye(4) if pose is None else np.asarray(pose, dtype=float)
    return [
        (
            chamfer_cylinder(plate / 2.0, 0.016, sections=28),
            pose @ transform((0.0, 0.0, 0.008)),
            mat,
        ),
        (
            trimesh.creation.cylinder(radius=plate * 0.16, height=0.05, sections=16),
            pose @ transform((0.0, 0.0, 0.041)),
            MAT_STEEL,
        ),
        (
            hex_bolt(plate * 0.46, 0.014),
            pose @ transform((0.0, 0.0, 0.052)),
            MAT_STEEL,
        ),
    ]


def bolt_circle_parts(count, radius, across_flats, height, pose=None, mat=MAT_STEEL):
    pose = np.eye(4) if pose is None else np.asarray(pose, dtype=float)
    bolt = hex_bolt(across_flats, height)
    return [
        (
            bolt,
            pose
            @ transform(
                (
                    radius * math.cos(2.0 * math.pi * index / count),
                    radius * math.sin(2.0 * math.pi * index / count),
                    0.0,
                )
            ),
            mat,
        )
        for index in range(count)
    ]


def bolt_row_parts(points, across_flats, height, pose=None, mat=MAT_STEEL):
    pose = np.eye(4) if pose is None else np.asarray(pose, dtype=float)
    bolt = hex_bolt(across_flats, height)
    return [(bolt, pose @ transform(point), mat) for point in points]


def textured_material(image, metallic=0.0, roughness=0.78):
    return pyrender.MetallicRoughnessMaterial(
        baseColorFactor=(1.0, 1.0, 1.0, 1.0),
        metallicFactor=metallic,
        roughnessFactor=roughness,
        baseColorTexture=pyrender.Texture(source=image, source_channels="RGB"),
    )


def screen_material(image, glow=1.0):
    """A display reads as switched on only if it emits its own picture."""
    return pyrender.MetallicRoughnessMaterial(
        baseColorFactor=(1.0, 1.0, 1.0, 1.0),
        metallicFactor=0.0,
        roughnessFactor=0.30,
        baseColorTexture=pyrender.Texture(source=image, source_channels="RGB"),
        emissiveTexture=pyrender.Texture(source=image, source_channels="RGB"),
        emissiveFactor=(glow, glow, glow),
    )


def _textured_quad(vertices, image, metallic, roughness, mat=None):
    # Sampling on these quads runs bottom-up, so the artwork is flipped once
    # here and every drawing routine can work in normal reading order.
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    faces = np.array(((0, 1, 2), (0, 2, 3)))
    uv = np.array(((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)))
    mesh = trimesh.Trimesh(
        vertices=np.asarray(vertices, dtype=float),
        faces=faces,
        process=False,
    )
    mesh.visual = trimesh.visual.TextureVisuals(uv=uv, image=image)
    return pyrender.Mesh.from_trimesh(
        mesh,
        material=mat if mat is not None else textured_material(image, metallic, roughness),
        smooth=False,
    )


def floor_plane_mesh(width, depth, image, metallic=0.10, roughness=0.80):
    """Painted concrete: image left edge is -X, image top edge is +Y."""
    half_w, half_d = width / 2.0, depth / 2.0
    return _textured_quad(
        (
            (-half_w, -half_d, 0.0),
            (half_w, -half_d, 0.0),
            (half_w, half_d, 0.0),
            (-half_w, half_d, 0.0),
        ),
        image,
        metallic,
        roughness,
    )


def panel_mesh(width, height, image, metallic=0.06, roughness=0.52, mat=None):
    """An upright plate that faces +Y and reads from that side."""
    half_w, half_h = width / 2.0, height / 2.0
    return _textured_quad(
        (
            (half_w, 0.0, -half_h),
            (-half_w, 0.0, -half_h),
            (-half_w, 0.0, half_h),
            (half_w, 0.0, half_h),
        ),
        image,
        metallic,
        roughness,
        mat,
    )


@dataclass
class RobotVisual:
    node: pyrender.Node
    link: str
    local_pose: np.ndarray


@dataclass
class ArmActor:
    robot: UR15
    puck_node: pyrender.Node
    collar_node: pyrender.Node
    cell_index: int
    side: str
    operation: str
    base_local_pose: np.ndarray
    pick_local_pose: np.ndarray
    drop_local_pose: np.ndarray


@dataclass
class RotatingNode:
    node: pyrender.Node
    cell_index: int
    local_pose: np.ndarray
    lifts: bool


@dataclass
class ConveyorItem:
    node: pyrender.Node
    offset: float
    local_pose: np.ndarray
    required_stage: int


@dataclass
class Palletiser:
    """The take-off robot that stacks finished units into the stocker."""

    robot: UR15
    keyframes: tuple
    carried_node: pyrender.Node
    outfeed_node: pyrender.Node
    stacked_node: pyrender.Node
    outfeed_pose: np.ndarray
    stacked_pose: np.ndarray


@dataclass
class DynamicNode:
    """Station hardware driven directly by the transfer cycle."""

    node: pyrender.Node
    base_pose: np.ndarray
    kind: str


@dataclass
class HarnessActor:
    cell_index: int
    operation: str
    segment_nodes: list[pyrender.Node]


@dataclass
class SharedObjectActor:
    cell_index: int
    operation: str
    node: pyrender.Node
    center_z_offset: float
    final_z: float


class UR15:
    VISUAL_CACHE: dict[str, list[tuple[pyrender.Mesh, np.ndarray, str]]] = {}
    GRIPPER_CACHE: dict[str, list[pyrender.Mesh]] = {}
    KINEMATICS = (
        ((0.0, 0.0, 0.2186), (0.0, 0.0, 0.0)),
        ((0.0, 0.0, 0.0), (math.pi / 2, 0.0, 0.0)),
        ((-0.6475, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ((-0.5164, 0.0, 0.1824), (0.0, 0.0, 0.0)),
        ((0.0, -0.1361, 0.0), (math.pi / 2, 0.0, 0.0)),
        ((0.0, 0.1434, 0.0), (math.pi / 2, math.pi, math.pi)),
    )
    LINKS = (
        "shoulder",
        "upper_arm",
        "forearm",
        "wrist_1",
        "wrist_2",
        "wrist_3",
    )
    MESHES = {
        "base": "base.dae",
        "shoulder": "shoulder.dae",
        "upper_arm": "upperarm.dae",
        "forearm": "forearm.dae",
        "wrist_1": "wrist1.dae",
        "wrist_2": "wrist2.dae",
        "wrist_3": "wrist3.dae",
    }
    VISUAL_OFFSETS = {
        "base": transform(rpy=(0.0, 0.0, math.pi)),
        "shoulder": transform(rpy=(0.0, 0.0, math.pi)),
        "upper_arm": transform(xyz=(0.0, 0.0, 0.100), rpy=(math.pi / 2, 0.0, -math.pi / 2)),
        "forearm": transform(xyz=(0.0, 0.0, 0.125), rpy=(math.pi / 2, 0.0, -math.pi / 2)),
        "wrist_1": transform(xyz=(0.0, 0.0, -0.0502), rpy=(math.pi / 2, 0.0, 0.0)),
        "wrist_2": transform(xyz=(0.0, 0.0, -0.064)),
        "wrist_3": transform(xyz=(0.0, 0.0, -0.0715), rpy=(math.pi / 2, 0.0, 0.0)),
    }

    def __init__(self, scene, base_pose):
        self.scene = scene
        self.base_pose = base_pose
        self.visuals: list[RobotVisual] = []
        self.gripper_visuals: list[RobotVisual] = []
        self._load_visual("base")
        for link in self.LINKS:
            self._load_visual(link)
        self._build_gripper()

    def _load_visual(self, link):
        if link not in self.VISUAL_CACHE:
            source = trimesh.load(MESH_ROOT / self.MESHES[link], force="scene")
            cached = []
            for graph_node in source.graph.nodes_geometry:
                local_pose, geometry_name = source.graph.get(graph_node)
                geometry = source.geometry[geometry_name]
                mesh = pyrender.Mesh.from_trimesh(geometry, smooth=False)
                cached.append(
                    (
                        mesh,
                        self.VISUAL_OFFSETS[link] @ local_pose,
                        str(graph_node),
                    )
                )
            self.VISUAL_CACHE[link] = cached
        for mesh, local_pose, graph_node in self.VISUAL_CACHE[link]:
            node = self.scene.add(mesh, pose=np.eye(4), name=f"{link}:{graph_node}")
            self.visuals.append(
                RobotVisual(
                    node=node,
                    link=link,
                    local_pose=local_pose,
                )
            )

    def _load_gripper_visual(self, link, filename, material_override=None):
        cache_key = f"{filename}:{'override' if material_override else 'source'}"
        if cache_key not in self.GRIPPER_CACHE:
            source = trimesh.load(ROBOTIQ_MESH_ROOT / filename, force="scene")
            cached = []
            for graph_node in source.graph.nodes_geometry:
                local_pose, geometry_name = source.graph.get(graph_node)
                geometry = source.geometry[geometry_name].copy()
                geometry.apply_transform(local_pose)
                geometry.apply_scale(0.001)
                cached.append(
                    pyrender.Mesh.from_trimesh(
                        geometry,
                        material=material_override,
                        smooth=False,
                    )
                )
            self.GRIPPER_CACHE[cache_key] = cached
        for mesh in self.GRIPPER_CACHE[cache_key]:
            node = self.scene.add(mesh, pose=np.eye(4), name=f"2f85:{link}")
            self.gripper_visuals.append(RobotVisual(node=node, link=link, local_pose=np.eye(4)))

    def _build_gripper(self):
        # BSD-licensed Robotiq 2F-85 visualization meshes from the
        # ros-industrial-attic/robotiq package.
        self._load_gripper_visual("gripper_base", "robotiq_gripper_coupling.stl", MAT_BRUSHED)
        self._load_gripper_visual("gripper_base", "robotiq_arg2f_85_base_link.dae")
        for side in ("left", "right"):
            self._load_gripper_visual(
                f"{side}_outer_knuckle",
                "robotiq_arg2f_85_outer_knuckle.dae",
                MAT_BRUSHED,
            )
            self._load_gripper_visual(
                f"{side}_outer_finger",
                "robotiq_arg2f_85_outer_finger.dae",
            )
            self._load_gripper_visual(
                f"{side}_inner_knuckle",
                "robotiq_arg2f_85_inner_knuckle.dae",
            )
            self._load_gripper_visual(
                f"{side}_inner_finger",
                "robotiq_arg2f_85_inner_finger.dae",
            )
            pad = self.scene.add(
                box_mesh((0.022, 0.00635, 0.0375), MAT_BLACK),
                pose=np.eye(4),
                name=f"2f85:{side}_pad",
            )
            self.gripper_visuals.append(
                RobotVisual(
                    node=pad,
                    link=f"{side}_pad",
                    local_pose=np.eye(4),
                )
            )

    @classmethod
    def forward(cls, base_pose, joints):
        base_inertia = base_pose @ transform(rpy=(0.0, 0.0, math.pi))
        poses = {"base": base_inertia}
        current = base_inertia
        for link, joint, (xyz, rpy) in zip(cls.LINKS, joints, cls.KINEMATICS):
            current = current @ transform(xyz, rpy) @ rotate_z(joint)
            poses[link] = current
        flange = current @ transform(rpy=(0.0, -math.pi / 2, -math.pi / 2))
        tool0 = flange @ transform(rpy=(math.pi / 2, 0.0, math.pi / 2))
        return poses, tool0

    def link_poses(self, joints):
        return self.forward(self.base_pose, joints)

    def update(self, joints, grip):
        poses, tool0 = self.link_poses(joints)
        for visual in self.visuals:
            self.scene.set_pose(visual.node, pose=poses[visual.link] @ visual.local_pose)
        q = 0.8 * grip
        gripper_poses = {"gripper_base": tool0}
        for side, reflect in (("left", 1.0), ("right", -1.0)):
            base_rotation = (1.0 + reflect) * math.pi / 2.0
            outer_knuckle = (
                tool0
                @ transform(
                    (0.0, reflect * -0.0306011, 0.054904),
                    rpy=(0.0, 0.0, base_rotation),
                )
                @ transform(rpy=(q, 0.0, 0.0))
            )
            outer_finger = outer_knuckle @ transform((0.0, 0.0315, -0.0041))
            inner_knuckle = (
                tool0
                @ transform(
                    (0.0, reflect * -0.0127, 0.06142),
                    rpy=(0.0, 0.0, base_rotation),
                )
                @ transform(rpy=(q, 0.0, 0.0))
            )
            inner_finger = outer_finger @ transform((0.0, 0.0061, 0.0471)) @ transform(rpy=(-q, 0.0, 0.0))
            gripper_poses.update(
                {
                    f"{side}_outer_knuckle": outer_knuckle,
                    f"{side}_outer_finger": outer_finger,
                    f"{side}_inner_knuckle": inner_knuckle,
                    f"{side}_inner_finger": inner_finger,
                    f"{side}_pad": inner_finger @ transform((0.0, -0.0220203446692936, 0.03242)),
                }
            )
        for visual in self.gripper_visuals:
            self.scene.set_pose(
                visual.node,
                pose=gripper_poses[visual.link] @ visual.local_pose,
            )
        return tool0


CELL_LAYOUT = tuple(
    (
        -CELL_X_OFFSET if index % 2 == 0 else CELL_X_OFFSET,
        CELL_Y_START + CELL_Y_SPACING * index,
        -math.pi / 2 if index % 2 == 0 else math.pi / 2,
    )
    for index in range(10)
)
CELL_OPERATIONS = (
    "housing_load",
    "connector_insert",
    "main_route",
    "branch_route",
    "clip_seat",
    "strain_relief",
    "cover_place",
    "latch_press",
    "electrical_test",
    "vision_inspect",
)
# Test and inspection stations carry fixed end effectors. They have nothing to
# collect, so they get no stocker and never turn away from the line: they
# simply retract above the conveyor between pallets.
INSPECTION_STATIONS = ("electrical_test", "vision_inspect")

# The stations share a cycle, not a choreography. Each one has its own work
# content, so it uses its own slice of the dwell in its own way: a probe holds
# still while it measures, a latch head taps three times, a cover comes down
# slowly and a routing pass sweeps the length of the channel. Entries are
# (style, delay after clamp, span of the stroke, extra), where extra is a hold
# time for the place and probe styles and a stroke count for press.
STATION_WORK = {
    "housing_load": ("place", 0.00, 1.95, 0.14),
    "connector_insert": ("insert", 0.10, 1.55, 0.0),
    "main_route": ("sweep", 0.05, 2.30, 0.0),
    "branch_route": ("sweep", 0.22, 1.80, 0.0),
    "clip_seat": ("press", 0.08, 1.70, 2),
    "strain_relief": ("place", 0.16, 1.55, 0.55),
    "cover_place": ("place", 0.00, 2.25, 0.16),
    "latch_press": ("press", 0.12, 1.75, 2),
    "electrical_test": ("probe", 0.05, 1.30, 1.10),
    "vision_inspect": ("scan", 0.10, 2.35, 0.0),
}
# Independent station controllers do not release on the same tick, and their
# tables do not swing at exactly the same rate.
CELL_TIMING_OFFSET = (
    0.00,
    0.10,
    -0.07,
    0.14,
    0.05,
    -0.10,
    0.12,
    -0.04,
    0.08,
    -0.12,
)


def station_work(operation):
    """Station programme with every duration stretched to the film's pace."""
    style, begin, span, extra = STATION_WORK[operation]
    if style in ("place", "probe"):
        extra = extra * PACE
    return style, begin * PACE, span * PACE, extra


def station_phases(operation):
    """Key moments of one station's work, in cycle-phase seconds."""
    style, begin, span, extra = station_work(operation)
    start = WORK_START + begin
    if style == "place":
        seat = start + span * 0.68
        release = seat + extra
        finish = start + span + extra
    elif style == "insert":
        seat = start + span * 0.70
        release = seat + 0.04 * PACE
        finish = start + span
    elif style == "sweep":
        seat = start + span * 0.62
        release = start + span * 0.80
        finish = start + span
    elif style == "press":
        seat = start + span * 0.72
        release = seat + 0.05 * PACE
        finish = start + span
    elif style == "probe":
        seat = start + span * 0.34
        release = seat + extra
        finish = start + span + extra
    else:
        seat = start + span * 0.50
        release = seat
        finish = start + span
    return {
        "start": start,
        "seat": seat,
        "release": release,
        "finish": finish,
    }


def cell_timing(cell_index):
    """Per-cell offsets for the table swing and the stocker pick."""
    shift = CELL_TIMING_OFFSET[cell_index] * PACE
    out_start = TURN_OUT_START + shift
    out_time = TURN_OUT_TIME + shift * 0.4
    return {
        "shift": shift,
        "back_time": TURN_BACK_TIME + shift * 0.6,
        "out_start": out_start,
        "out_time": out_time,
        "hold": out_start + out_time * 0.55,
        "ready": out_start + out_time,
    }


STATION_PHASES = tuple(station_phases(op) for op in CELL_OPERATIONS)


def fetches_component(cell_index):
    return CELL_OPERATIONS[cell_index] not in INSPECTION_STATIONS


def single_arm(cell_index):
    """Test and inspection carry one head over the work, so one arm does it.

    The other eight stations need two hands: they lift a part between them or
    work opposite ends of the same product at once. Measuring and looking do
    not, so those cells get a single UR15 on one arm of the yoke.
    """
    return CELL_OPERATIONS[cell_index] in INSPECTION_STATIONS


# The line is balanced: every station shares the same cycle, so all ten cells
# work during the same dwell and the whole line indexes together.


# ---------------------------------------------------------------------------
# The product: an EV junction box and its HV harness.
#
# These parts sit closest to the camera and are instanced twenty-two times, so
# each is built once as a proper assembly — enclosure, flange, glands, latches
# — and merged into a single mesh. The cost is the same as the box it replaces.
# ---------------------------------------------------------------------------


def pallet_assembly_mesh():
    """Tooling plate on runners, with the bushes the station pins engage."""
    parts = [
        (chamfer_box((0.64, 0.84, 0.030), 0.005), transform((0.0, 0.0, 0.0175)), MAT_ALUMINUM),
    ]
    for rail_x in (-0.26, 0.26):
        parts.append(
            (
                chamfer_box((0.09, 0.84, 0.036), 0.005),
                transform((rail_x, 0.0, -0.0145)),
                MAT_BRUSHED,
            )
        )
    for rail_y in (-0.36, 0.36):
        parts.append(
            (
                chamfer_box((0.46, 0.08, 0.030), 0.004),
                transform((0.0, rail_y, -0.0125)),
                MAT_BRUSHED,
            )
        )
    for bush_x in (-0.12, 0.12):
        parts.append(
            (
                trimesh.creation.annulus(r_min=0.013, r_max=0.024, height=0.030),
                transform((bush_x, 0.0, -0.017)),
                MAT_STEEL,
            )
        )
    # Corner nests that locate the housing, and the pallet's ID plate.
    for nest_x in (-0.285, 0.285):
        for nest_y in (-0.30, 0.30):
            parts.append(
                (
                    chamfer_box((0.036, 0.075, 0.034), 0.005),
                    transform((nest_x, nest_y, 0.0295)),
                    MAT_DARK_METAL,
                )
            )
    parts.append(
        (
            chamfer_box((0.095, 0.010, 0.045), 0.003),
            transform((0.20, -0.425, 0.006)),
            MAT_CABINET_TRIM,
        )
    )
    parts.extend(
        bolt_row_parts(
            [(x, y, 0.030) for x in (-0.26, 0.26) for y in (-0.30, 0.0, 0.30)],
            0.013,
            0.008,
        )
    )
    return assembly_mesh(parts)


def housing_assembly_mesh():
    """Cast enclosure: open on top, flanged foot, drafted side ribs."""
    wall = 0.024
    height = 0.11
    parts = [
        (
            chamfer_box((0.545, 0.765, 0.016), 0.005),
            transform((0.0, 0.0, -height / 2.0 + 0.008)),
            MAT_BRUSHED,
        ),
        (
            chamfer_box((0.50, 0.72, 0.020), 0.004),
            transform((0.0, 0.0, -height / 2.0 + 0.026)),
            MAT_BRUSHED,
        ),
    ]
    for wall_x in (-0.238, 0.238):
        parts.append(
            (
                chamfer_box((wall, 0.72, height - 0.030), 0.004),
                transform((wall_x, 0.0, 0.015)),
                MAT_BRUSHED,
            )
        )
    for wall_y in (-0.348, 0.348):
        parts.append(
            (
                chamfer_box((0.50 - 2.0 * wall, wall, height - 0.030), 0.004),
                transform((0.0, wall_y, 0.015)),
                MAT_BRUSHED,
            )
        )
    # Sealing rim the cover lands on.
    parts.append(
        (
            chamfer_box((0.512, 0.732, 0.010), 0.003),
            transform((0.0, 0.0, height / 2.0 - 0.005)),
            MAT_ALUMINUM,
        )
    )
    # Mounting bosses on the flange corners, each with its bolt.
    for boss_x in (-0.252, 0.252):
        for boss_y in (-0.352, 0.352):
            parts.append(
                (
                    chamfer_cylinder(0.024, 0.022, sections=20),
                    transform((boss_x, boss_y, -height / 2.0 + 0.011)),
                    MAT_BRUSHED,
                )
            )
            parts.append(
                (
                    hex_bolt(0.017, 0.010),
                    transform((boss_x, boss_y, -height / 2.0 + 0.022)),
                    MAT_STEEL,
                )
            )
    # Cast ribs down the long walls.
    for rib_y in np.linspace(-0.27, 0.27, 7):
        for rib_x in (-0.252, 0.252):
            parts.append(
                (
                    chamfer_box((0.012, 0.026, height - 0.046), 0.003),
                    transform((rib_x, rib_y, 0.012)),
                    MAT_BRUSHED,
                )
            )
    return assembly_mesh(parts)


def busbar_tray_mesh():
    """The terminal tray that drops onto the housing rim."""
    parts = [
        (chamfer_box((0.44, 0.63, 0.008), 0.002), transform((0.0, 0.0, -0.012)), MAT_DARK_METAL),
        (chamfer_box((0.38, 0.56, 0.014), 0.003), transform((0.0, 0.0, -0.001)), MAT_DARK_METAL),
    ]
    for rib_x in (-0.11, 0.0, 0.11):
        parts.append(
            (
                chamfer_box((0.010, 0.54, 0.022), 0.002),
                transform((rib_x, 0.0, 0.012)),
                MAT_DARK_METAL,
            )
        )
    for rib_y in (-0.205, 0.205):
        parts.append(
            (
                chamfer_box((0.36, 0.010, 0.018), 0.002),
                transform((0.0, rib_y, 0.010)),
                MAT_DARK_METAL,
            )
        )
    for block_x in (-0.055, 0.055):
        for block_y in (-0.115, 0.115):
            parts.append(
                (
                    chamfer_box((0.052, 0.030, 0.020), 0.003),
                    transform((block_x, block_y, 0.014)),
                    MAT_PUCK_BLUE,
                )
            )
            parts.append(
                (
                    hex_bolt(0.010, 0.006),
                    transform((block_x, block_y, 0.023)),
                    MAT_STEEL,
                )
            )
    return assembly_mesh(parts)


def cover_assembly_mesh():
    """Moulded lid: gasket lip under, stiffening ribs and a label pad over."""
    parts = [
        (fillet_box((0.43, 0.62, 0.030), 0.007), transform((0.0, 0.0, 0.003)), MAT_WHITE_SATIN),
        (chamfer_box((0.39, 0.58, 0.012), 0.003), transform((0.0, 0.0, -0.014)), MAT_DARK_METAL),
    ]
    for rib_x in (-0.155, -0.085, 0.085, 0.155):
        parts.append(
            (
                chamfer_box((0.013, 0.50, 0.010), 0.003),
                transform((rib_x, 0.0, 0.021)),
                MAT_WHITE_SATIN,
            )
        )
    parts.append(
        (
            chamfer_box((0.135, 0.095, 0.005), 0.002),
            transform((0.0, 0.16, 0.019)),
            MAT_WHITE,
        )
    )
    for screw_x in (-0.185, 0.185):
        for screw_y in (-0.275, 0.275):
            parts.append(
                (
                    chamfer_cylinder(0.017, 0.008, sections=18),
                    transform((screw_x, screw_y, 0.019)),
                    MAT_WHITE_SATIN,
                )
            )
            parts.append(
                (
                    hex_bolt(0.013, 0.007),
                    transform((screw_x, screw_y, 0.022)),
                    MAT_STEEL,
                )
            )
    return assembly_mesh(parts)


def cable_gland_mesh():
    """Cable entry: a gland body with its lock nut, facing both ways."""
    parts = [
        (chamfer_box((0.048, 0.086, 0.072), 0.006), None, MAT_BLACK),
    ]
    for sign in (-1.0, 1.0):
        parts.append(
            (
                trimesh.creation.cylinder(radius=0.026, height=0.014, sections=6),
                transform((sign * 0.028, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
                MAT_DARK_METAL,
            )
        )
        parts.append(
            (
                chamfer_cylinder(0.018, 0.016, sections=20),
                transform((sign * 0.042, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
                MAT_BLACK,
            )
        )
    for bolt_y in (-0.032, 0.032):
        parts.append((hex_bolt(0.011, 0.006), transform((0.0, bolt_y, 0.036)), MAT_STEEL))
    return assembly_mesh(parts)


def hv_connector_mesh():
    """Keyed HV connector: shell, latch, front flange and strain-relief boot."""
    parts = [
        (fillet_box((0.108, 0.068, 0.064), 0.008), None, MAT_HV_ORANGE),
        (
            chamfer_box((0.050, 0.030, 0.014), 0.004),
            transform((-0.012, 0.0, 0.036)),
            MAT_HV_ORANGE,
        ),
        (
            chamfer_box((0.014, 0.076, 0.074), 0.004),
            transform((0.060, 0.0, 0.0)),
            MAT_DARK_METAL,
        ),
        (
            chamfer_cylinder(0.024, 0.026, sections=22),
            transform((-0.066, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            MAT_HV_ORANGE,
        ),
        (
            chamfer_cylinder(0.018, 0.020, sections=22),
            transform((-0.086, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            MAT_BLACK,
        ),
    ]
    for bolt_z in (-0.026, 0.026):
        parts.append(
            (
                hex_bolt(0.011, 0.006),
                transform((0.067, 0.0, bolt_z), rpy=(0.0, math.pi / 2.0, 0.0)),
                MAT_STEEL,
            )
        )
    return assembly_mesh(parts)


def cable_clip_mesh():
    """Saddle clip: a U that actually surrounds the cable it holds."""
    parts = [
        (chamfer_box((0.052, 0.044, 0.016), 0.004), transform((0.0, 0.0, -0.014)), MAT_PUCK_BLUE),
    ]
    for jaw_x in (-0.020, 0.020):
        parts.append(
            (
                chamfer_box((0.011, 0.044, 0.038), 0.003),
                transform((jaw_x, 0.0, 0.008)),
                MAT_PUCK_BLUE,
            )
        )
    parts.append((hex_bolt(0.010, 0.006), transform((0.0, 0.0, -0.020)), MAT_STEEL))
    return assembly_mesh(parts)


def strain_relief_mesh():
    """Clamp bar on two feet, bolted down over the harness."""
    parts = [
        (chamfer_box((0.062, 0.53, 0.014), 0.004), transform((0.0, 0.0, 0.012)), MAT_BRUSHED),
    ]
    for foot_y in (-0.245, 0.245):
        parts.append(
            (
                chamfer_box((0.062, 0.045, 0.038), 0.005),
                transform((0.0, foot_y, -0.004)),
                MAT_BRUSHED,
            )
        )
        parts.append((hex_bolt(0.015, 0.009), transform((0.0, foot_y, 0.018)), MAT_STEEL))
    for saddle_y in (-0.10, 0.10):
        parts.append(
            (
                chamfer_box((0.052, 0.032, 0.020), 0.004),
                transform((0.0, saddle_y, 0.005)),
                MAT_DARK_METAL,
            )
        )
    return assembly_mesh(parts)


def toggle_latch_mesh():
    """Draw latch: base, pivot and hook, the way a lid is actually held."""
    parts = [
        (chamfer_box((0.028, 0.052, 0.012), 0.003), transform((0.026, 0.0, -0.013)), MAT_DARK_METAL),
        (chamfer_box((0.066, 0.038, 0.011), 0.003), transform((-0.004, 0.0, 0.004)), MAT_BLACK),
        (chamfer_box((0.013, 0.030, 0.030), 0.003), transform((-0.032, 0.0, -0.004)), MAT_STEEL),
        (
            trimesh.creation.cylinder(radius=0.005, height=0.056, sections=14),
            transform((0.020, 0.0, 0.002), rpy=(math.pi / 2.0, 0.0, 0.0)),
            MAT_STEEL,
        ),
    ]
    return assembly_mesh(parts)


def terminal_stud_mesh():
    """Insulated stud with its nut, built about the local Z axis."""
    return assembly_mesh(
        [
            (chamfer_cylinder(0.030, 0.014, sections=26), None, MAT_HV_ORANGE),
            (
                trimesh.creation.cylinder(radius=0.008, height=0.030, sections=14),
                transform((0.0, 0.0, 0.012)),
                MAT_STEEL,
            ),
            (hex_bolt(0.017, 0.008), transform((0.0, 0.0, 0.010)), MAT_STEEL),
        ]
    )


def add_rotating_part(
    scene,
    rotating_nodes,
    cell_index,
    mesh,
    local_pose,
    lifts=True,
):
    node = scene.add(mesh, pose=np.eye(4))
    rotating_nodes.append(
        RotatingNode(
            node=node,
            cell_index=cell_index,
            local_pose=local_pose,
            lifts=lifts,
        )
    )


def add_assembly_cell(scene, cell_index, center):
    cx, cy = center
    rotating_nodes: list[RotatingNode] = []

    # Fixed service plinth and the lower stator of the 360-degree table:
    # grouted baseplate, anchor bolts, bearing housing and its cable entry.
    plinth_parts = [
        (chamfer_box((0.56, 0.60, 0.070), 0.008), transform((0.0, 0.0, -0.005)), MAT_WHITE_SATIN),
        (chamfer_box((0.50, 0.54, 0.025), 0.005), transform((0.0, 0.0, 0.048)), MAT_WHITE),
        (
            chamfer_cylinder(LOWER_BASE_RADIUS, 0.15, sections=64),
            transform((0.0, 0.0, 0.145)),
            MAT_BLACK,
        ),
    ]
    plinth_parts.extend(
        bolt_row_parts(
            [(x, y, 0.030) for x in (-0.245, 0.245) for y in (-0.265, 0.265)],
            0.026,
            0.016,
        )
    )
    plinth_parts.extend(bolt_circle_parts(8, 0.188, 0.017, 0.010, transform((0.0, 0.0, 0.215))))
    plinth_parts.append(
        (
            chamfer_box((0.15, 0.11, 0.15), 0.006),
            transform((0.0, 0.255, 0.115)),
            MAT_CABINET_TRIM,
        )
    )
    plinth_parts.append(
        (
            chamfer_cylinder(0.030, 0.06, sections=18),
            transform((0.0, 0.315, 0.16), rpy=(math.pi / 2.0, 0.0, 0.0)),
            MAT_HOSE,
        )
    )
    scene.add(assembly_mesh(plinth_parts), pose=transform((cx, cy, 0.0)))

    # Everything above the bearing rotates together, and everything above the
    # telescopic sleeve also rises with the lift; each group is one mesh.
    turret_parts = [
        (
            chamfer_cylinder(0.20, 0.105, sections=64),
            transform((0.0, 0.0, 0.245)),
            MAT_WHITE_SATIN,
        ),
        (
            chamfer_cylinder(0.15, 0.10, sections=56),
            transform((0.0, 0.0, 0.34)),
            MAT_BRUSHED,
        ),
    ]
    turret_parts.extend(bolt_circle_parts(6, 0.168, 0.015, 0.009, transform((0.0, 0.0, 0.296))))
    # Way cover over the telescopic sleeve, built as the bellows it is.
    for index in range(8):
        ring_z = 0.315 + index * 0.0465
        radius = 0.128 if index % 2 == 0 else 0.108
        turret_parts.append(
            (
                chamfer_cylinder(radius, 0.040, chamfer=0.008, sections=44),
                transform((0.0, 0.0, ring_z)),
                MAT_DARK_METAL,
            )
        )
    # Drive box and the umbilical that feeds the moving head.
    turret_parts.append(
        (
            chamfer_box((0.13, 0.16, 0.22), 0.008),
            transform((0.0, 0.245, 0.40)),
            MAT_CABINET_TRIM,
        )
    )
    turret_parts.append(
        (
            chamfer_box((0.075, 0.05, 0.30), 0.006),
            transform((0.0, 0.215, 0.60)),
            MAT_DUCT,
        )
    )
    add_rotating_part(
        scene,
        rotating_nodes,
        cell_index,
        assembly_mesh(turret_parts),
        np.eye(4),
        lifts=False,
    )

    column_parts = [
        (
            chamfer_cylinder(T_FRAME_RADIUS, T_FRAME_STEM_HEIGHT, chamfer=0.010, sections=56),
            transform((0.0, 0.0, T_FRAME_STEM_BOTTOM + T_FRAME_STEM_HEIGHT / 2.0)),
            MAT_WHITE_SATIN,
        ),
    ]
    for collar_z in (0.62, 1.16):
        column_parts.append(
            (
                chamfer_cylinder(T_FRAME_RADIUS + 0.012, 0.030, sections=48),
                transform((0.0, 0.0, collar_z)),
                MAT_BRUSHED,
            )
        )
        column_parts.extend(
            bolt_circle_parts(
                4,
                T_FRAME_RADIUS + 0.004,
                0.013,
                0.008,
                transform((0.0, 0.0, collar_z + 0.016)),
            )
        )
    # Cable duct up the back of the column, with its junction box.
    column_parts.append(
        (
            chamfer_box((0.075, 0.055, 0.72), 0.006),
            transform((0.0, T_FRAME_RADIUS + 0.022, 0.86)),
            MAT_DUCT,
        )
    )
    column_parts.append(
        (
            chamfer_box((0.11, 0.085, 0.16), 0.007),
            transform((0.0, T_FRAME_RADIUS + 0.030, 1.30)),
            MAT_CABINET_TRIM,
        )
    )
    for gland_x in (-0.030, 0.030):
        column_parts.append(
            (
                chamfer_cylinder(0.016, 0.030, sections=16),
                transform(
                    (gland_x, T_FRAME_RADIUS + 0.030, 1.215),
                    rpy=(0.0, 0.0, 0.0),
                ),
                MAT_HOSE,
            )
        )
    # Industrial stereo head in the crotch of the Y, pitched 45 degrees down
    # so its field of view sits on the work. From here the station's own work
    # points lie between 31 and 45 degrees below horizontal, so this is where
    # a real cell would put it.
    camera_pose = transform(
        (0.0, -0.175, SHOULDER_HEIGHT - 0.045),
        rpy=(math.radians(135.0), 0.0, 0.0),
    )
    column_parts.append((chamfer_box((0.24, 0.085, 0.075), 0.007), camera_pose, MAT_CABINET_TRIM))
    column_parts.append(
        (
            chamfer_box((0.20, 0.030, 0.020), 0.004),
            camera_pose @ transform((0.0, -0.030, 0.046)),
            MAT_BRUSHED,
        )
    )
    for lens_x, lens_radius, lens_material in (
        (-0.088, 0.021, MAT_DARK_METAL),
        (0.0, 0.026, MAT_BRUSHED),
        (0.088, 0.021, MAT_DARK_METAL),
    ):
        column_parts.append(
            (
                chamfer_cylinder(lens_radius, 0.028, sections=26),
                camera_pose @ transform((lens_x, 0.0, 0.050)),
                lens_material,
            )
        )
        # Lens hood, then the glass inside it.
        column_parts.append(
            (
                trimesh.creation.annulus(
                    r_min=lens_radius * 0.86,
                    r_max=lens_radius * 1.14,
                    height=0.014,
                    sections=26,
                ),
                camera_pose @ transform((lens_x, 0.0, 0.070)),
                MAT_DARK_METAL,
            )
        )
        column_parts.append(
            (
                chamfer_cylinder(lens_radius * 0.72, 0.006, sections=24),
                camera_pose @ transform((lens_x, 0.0, 0.066)),
                MAT_CYAN,
            )
        )
    # Illuminator bar and the M12 lead leaving the head.
    column_parts.append(
        (
            chamfer_box((0.19, 0.022, 0.014), 0.003),
            camera_pose @ transform((0.0, 0.030, 0.044)),
            MAT_LAMP_OFF,
        )
    )
    column_parts.append(
        (
            chamfer_cylinder(0.011, 0.026, sections=14),
            camera_pose @ transform((0.10, 0.0, -0.020), rpy=(0.0, math.pi / 2.0, 0.0)),
            MAT_DARK_METAL,
        )
    )
    column_parts.append(
        (
            chamfer_box((0.06, 0.12, 0.030), 0.005),
            transform((0.0, -0.105, SHOULDER_HEIGHT - 0.015)),
            MAT_BRUSHED,
        )
    )
    column_parts.append(
        (
            trimesh.creation.cylinder(radius=0.011, height=0.26, sections=12),
            transform(
                (0.055, -0.10, SHOULDER_HEIGHT - 0.10),
                rpy=(0.5, 0.0, 0.0),
            ),
            MAT_HOSE,
        )
    )

    # A Y yoke: the two arms rise away from the column instead of lying flat
    # across a T crossbar. A single-arm cell keeps one of them and caps the
    # other mounting, which is what a line does when it buys one robot for a
    # station rather than two.
    arms = (-1.0,) if single_arm(cell_index) else (-1.0, 1.0)
    if single_arm(cell_index):
        column_parts.append(
            (
                chamfer_cylinder(T_FRAME_RADIUS * 0.98, 0.045, sections=44),
                transform((0.0, 0.0, SHOULDER_HEIGHT + 0.010)),
                MAT_BRUSHED,
            )
        )
        column_parts.extend(
            bolt_circle_parts(
                6,
                T_FRAME_RADIUS * 0.72,
                0.014,
                0.009,
                transform((0.0, 0.0, SHOULDER_HEIGHT + 0.032)),
            )
        )
    for sign in arms:
        arm_pose = cylinder_between_pose(
            (0.0, 0.0, SHOULDER_HEIGHT - 0.06),
            (sign * YOKE_SPREAD, 0.0, SHOULDER_HEIGHT + YOKE_RISE),
        )
        column_parts.append(
            (
                chamfer_cylinder(T_FRAME_RADIUS * 0.94, 1.0, chamfer=0.008, sections=44),
                arm_pose,
                MAT_WHITE_SATIN,
            )
        )
        flange_pose = transform(
            (sign * YOKE_SPREAD, 0.0, SHOULDER_HEIGHT + YOKE_RISE),
            rpy=(0.0, sign * (math.pi / 2.0 - YOKE_ANGLE), 0.0),
        )
        column_parts.append(
            (
                chamfer_cylinder(T_FRAME_RADIUS * 1.14, 0.05, sections=44),
                flange_pose,
                MAT_BRUSHED,
            )
        )
        column_parts.extend(
            bolt_circle_parts(
                6,
                T_FRAME_RADIUS * 0.98,
                0.015,
                0.009,
                flange_pose @ transform((0.0, 0.0, -0.030)),
                mat=MAT_STEEL,
            )
        )
        # Gusset in the crotch, where a fabricated yoke would be stiffened.
        column_parts.append(
            (
                chamfer_box((0.13, 0.016, 0.14), 0.004),
                transform(
                    (sign * 0.055, 0.0, SHOULDER_HEIGHT - 0.085),
                    rpy=(0.0, sign * math.radians(28.0), 0.0),
                ),
                MAT_WHITE_SATIN,
            )
        )
    add_rotating_part(
        scene,
        rotating_nodes,
        cell_index,
        assembly_mesh(column_parts),
        np.eye(4),
    )
    return rotating_nodes


def stocker_component(operation):
    """The part a station is fed, as its own mesh and footprint.

    The same mesh the arms carry and the pallet ends up with, so what is
    waiting in the stocker is visibly the part that station fits.
    """
    if operation == "housing_load":
        return housing_assembly_mesh(), (0.545, 0.765, 0.110)
    if operation == "cover_place":
        return cover_assembly_mesh(), (0.430, 0.620, 0.042)
    if operation == "strain_relief":
        return strain_relief_mesh(), (0.062, 0.530, 0.046)
    if operation == "connector_insert":
        return hv_connector_mesh(), (0.150, 0.076, 0.074)
    if operation in ("main_route", "branch_route"):
        return (
            assembly_mesh(
                [
                    (fillet_box((0.070, 0.058, 0.048), 0.008), None, MAT_HV_ORANGE),
                    (
                        chamfer_box((0.020, 0.036, 0.036), 0.004),
                        transform((0.042, 0.0, 0.0)),
                        MAT_DARK_METAL,
                    ),
                ]
            ),
            (0.092, 0.058, 0.048),
        )
    if operation == "clip_seat":
        return cable_clip_mesh(), (0.052, 0.046, 0.050)
    if operation == "latch_press":
        return toggle_latch_mesh(), (0.078, 0.056, 0.032)
    return None, (0.0, 0.0, 0.0)


# How each station's parts are presented. Large parts the two arms lift
# together are stacked in a magazine the shape of the part; bars lie in a row;
# small components sit in pocketed trays, one pocket per pick.
STOCKER_STYLE = {
    "housing_load": "magazine",
    "cover_place": "magazine",
    "strain_relief": "bars",
    "connector_insert": "pockets",
    "main_route": "coils",
    "branch_route": "coils",
    "clip_seat": "pockets",
    "latch_press": "pockets",
}
STOCKER_STACK = {"housing_load": (4, 0.128), "cover_place": (6, 0.055)}


def add_stocker(scene, cell_index, cx, cy):
    """The stocker for one cell, built around the part it holds."""
    operation = CELL_OPERATIONS[cell_index]
    side = -1.0 if cx < 0 else 1.0
    style = STOCKER_STYLE[operation]
    part, extent = stocker_component(operation)
    points = stock_pick_points(cell_index)
    pick_x = float(points[0][0])
    pick_z = float(points[0][2])
    inner_x = side * STOCKER_INNER_X
    outer_x = side * STOCKER_OUTER_X
    centre_x = (inner_x + outer_x) / 2.0
    frame = []

    def upright(x, y, height, base):
        frame.extend(extrusion_parts(0.040, height, transform((x, y, base + height / 2.0))))
        frame.extend(levelling_foot_parts(transform((x, y, 0.0)), plate=0.09))

    if style in ("magazine", "bars"):
        # A cantilever rack: posts only on the outboard side, so the stack of
        # parts is not fighting an upright standing in the middle of it.
        deck_z = pick_z - extent[0] / 2.0 - 0.055 if style == "magazine" else pick_z - extent[2] / 2.0 - 0.030
        for post_y in (cy - 0.43, cy + 0.43):
            upright(outer_x, post_y, 1.30, 0.02)
            frame.extend(
                extrusion_parts(
                    0.040,
                    abs(outer_x - (pick_x - side * extent[0] * 0.62)),
                    transform(
                        (
                            (outer_x + pick_x - side * extent[0] * 0.62) / 2.0,
                            post_y,
                            deck_z - 0.030,
                        ),
                        rpy=(0.0, math.pi / 2.0, 0.0),
                    ),
                )
            )
            # Gusset back to the post.
            frame.append(
                (
                    chamfer_box((0.16, 0.010, 0.16), 0.004),
                    transform(
                        (outer_x - side * 0.10, post_y, deck_z - 0.115),
                        rpy=(0.0, side * math.pi / 4.0, 0.0),
                    ),
                    MAT_BRUSHED,
                )
            )
        row = (
            STOCKER_STACK[operation][0] * STOCKER_STACK[operation][1] + 0.12
            if style == "magazine"
            else extent[0] + 0.10
        )
        frame.append(
            (
                chamfer_box((row, extent[1] + 0.14, 0.022), 0.004),
                transform(
                    (
                        pick_x + side * (row / 2.0 - 0.09) if style == "magazine" else pick_x,
                        cy,
                        deck_z - 0.011,
                    )
                ),
                MAT_BRUSHED,
            )
        )
        for rail_z in (0.16, 1.24):
            frame.extend(
                extrusion_parts(
                    0.040,
                    0.89,
                    transform((outer_x, cy, rail_z), rpy=(math.pi / 2.0, 0.0, 0.0)),
                )
            )
    else:
        # Four-post rack with a shelf at each pick.
        for rack_x in (inner_x, outer_x):
            for rack_y in (cy - 0.43, cy + 0.43):
                upright(rack_x, rack_y, 1.22, 0.04)
        for rail_z in (0.12, 1.24):
            for rack_x in (inner_x, outer_x):
                frame.extend(
                    extrusion_parts(
                        0.040,
                        0.89,
                        transform((rack_x, cy, rail_z), rpy=(math.pi / 2.0, 0.0, 0.0)),
                    )
                )
            for rack_y in (cy - 0.43, cy + 0.43):
                frame.extend(
                    extrusion_parts(
                        0.040,
                        0.35,
                        transform(
                            (centre_x, rack_y, rail_z),
                            rpy=(0.0, math.pi / 2.0, 0.0),
                        ),
                    )
                )

    if style == "magazine":
        count, pitch = STOCKER_STACK[operation]
        # Panels stand on edge in the rack, the way sheet parts are stored,
        # so the hands take one on edge, carry it on edge and only lay it
        # down onto the pallet. Nothing turns it in between.
        upright = transform(rpy=(0.0, math.pi / 2.0, 0.0))
        for level in range(count):
            slot_x = pick_x + side * level * pitch
            scene.add(part, pose=transform((slot_x, cy, pick_z)) @ upright)
            # A divider behind each panel, and a foot it stands on.
            frame.append(
                (
                    chamfer_box((0.012, extent[1] + 0.06, extent[0] * 0.62), 0.003),
                    transform(
                        (
                            slot_x + side * pitch * 0.5,
                            cy,
                            pick_z - extent[0] * 0.18,
                        )
                    ),
                    MAT_DARK_METAL,
                )
            )
        for foot_y in (cy - extent[1] * 0.34, cy + extent[1] * 0.34):
            frame.append(
                (
                    chamfer_box((count * pitch + 0.10, 0.040, 0.030), 0.004),
                    transform(
                        (
                            pick_x + side * (count - 1) * pitch / 2.0,
                            foot_y,
                            deck_z + 0.015,
                        )
                    ),
                    MAT_ALUMINUM,
                )
            )
        # Side guides that keep the row square.
        for guide_y in (
            cy - extent[1] / 2.0 - 0.030,
            cy + extent[1] / 2.0 + 0.030,
        ):
            height = pick_z + extent[0] * 0.5 + 0.04 - deck_z
            frame.append(
                (
                    chamfer_box((count * pitch + 0.10, 0.026, 0.026), 0.004),
                    transform(
                        (
                            pick_x + side * (count - 1) * pitch / 2.0,
                            guide_y,
                            pick_z + extent[0] * 0.45,
                        )
                    ),
                    MAT_ALUMINUM,
                )
            )
            for post_x in (pick_x - side * 0.04, pick_x + side * ((count - 1) * pitch + 0.04)):
                frame.append(
                    (
                        chamfer_box((0.030, 0.030, height), 0.005),
                        transform((post_x, guide_y, deck_z + height / 2.0)),
                        MAT_ALUMINUM,
                    )
                )
    elif style == "bars":
        # Bars lying in a row of notched supports, the front one on the picks.
        for index in range(5):
            bar_x = pick_x + side * index * 0.085
            scene.add(part, pose=transform((bar_x, cy, pick_z)))
            for notch_y in (cy - 0.20, cy + 0.20):
                frame.append(
                    (
                        chamfer_box((0.020, 0.055, 0.055), 0.004),
                        transform((bar_x, notch_y, pick_z - 0.048)),
                        MAT_DARK_METAL,
                    )
                )
    else:
        # Pocketed trays: one pocket per pick, the rest of the grid holding
        # the spares that station will use next.
        pocket_x, pocket_y = extent[0] + 0.030, extent[1] + 0.026
        for point in points:
            tray_y = float(point[1])
            frame.append(
                (
                    chamfer_box((0.34, 0.28, 0.018), 0.004),
                    transform((centre_x, tray_y, pick_z - extent[2] / 2.0 - 0.010)),
                    MAT_BRUSHED,
                )
            )
            for bracket_y in (tray_y - 0.11, tray_y + 0.11):
                frame.append(
                    (
                        chamfer_box((0.32, 0.008, 0.034), 0.003),
                        transform((centre_x, bracket_y, pick_z - extent[2] / 2.0 - 0.036)),
                        MAT_ALUMINUM,
                    )
                )
            columns = max(2, int(0.30 // pocket_x))
            rows = max(1, int(0.24 // pocket_y))
            for column in range(columns):
                for row in range(rows):
                    slot_x = centre_x + side * ((columns - 1) / 2.0 - column) * pocket_x
                    slot_y = tray_y + ((rows - 1) / 2.0 - row) * pocket_y
                    if column == 0 and row == (rows - 1) // 2:
                        slot_x, slot_y = float(point[0]), tray_y
                    scene.add(part, pose=transform((slot_x, slot_y, pick_z)))
                    for wall in (
                        (pocket_x * 0.5, 0.0, 0.006, pocket_y),
                        (0.0, pocket_y * 0.5, pocket_x, 0.006),
                    ):
                        frame.append(
                            (
                                chamfer_box((wall[2], wall[3], extent[2] + 0.014), 0.002),
                                transform(
                                    (slot_x + wall[0], slot_y + wall[1], pick_z),
                                ),
                                MAT_DARK_METAL,
                            )
                        )
            frame.append(
                (
                    chamfer_box((0.020, 0.26, 0.10), 0.004),
                    transform((outer_x, tray_y, pick_z - 0.012)),
                    MAT_DARK_METAL,
                )
            )
            frame.append(
                (
                    chamfer_box((0.014, 0.22, 0.045), 0.003),
                    transform((inner_x - side * 0.012, tray_y, pick_z - 0.070)),
                    MAT_WHITE,
                )
            )
        if style == "coils":
            # The cable these lengths are cut from, on its spindle.
            frame.append(
                (
                    chamfer_cylinder(0.030, 0.30, sections=20),
                    transform((centre_x, cy, 1.06), rpy=(0.0, math.pi / 2.0, 0.0)),
                    MAT_BRUSHED,
                )
            )
            for coil in range(3):
                frame.append(
                    (
                        trimesh.creation.torus(
                            major_radius=0.115,
                            minor_radius=0.016,
                            major_sections=28,
                            minor_sections=8,
                        ),
                        transform(
                            (centre_x + side * (coil - 1) * 0.045, cy, 1.06),
                            rpy=(0.0, math.pi / 2.0, 0.0),
                        ),
                        MAT_HV_ORANGE,
                    )
                )
    scene.add(assembly_mesh(frame))


def add_environment(scene):
    rotating_nodes: list[RotatingNode] = []
    conveyor_items: list[ConveyorItem] = []
    dynamic_nodes: list[DynamicNode] = []

    # The slab sits well below the painted surface so the two never fight for
    # depth at grazing angles.
    scene.add(
        box_mesh((FLOOR_WIDTH, FLOOR_DEPTH, 0.60), MAT_CONCRETE),
        pose=transform((0.0, FLOOR_CENTER_Y, -0.45)),
    )
    scene.add(
        floor_plane_mesh(FLOOR_WIDTH, FLOOR_DEPTH, make_floor_texture()),
        pose=transform((0.0, FLOOR_CENTER_Y, -0.033)),
    )

    # Free-flow pallet conveyor: a driven roller bed carried between two
    # slotted aluminium side frames, on braced stands with levelling feet.
    # The rollers are what make it read as a conveyor rather than a plinth,
    # so they are modelled and merged rather than faked with a flat belt.
    deck_top = 0.3925
    roller_radius = 0.024
    roller_pitch = 0.115
    lie_along_x = transform(rpy=(0.0, math.pi / 2.0, 0.0))
    roller = chamfer_cylinder(roller_radius, 0.66, chamfer=0.004, sections=18)
    journal = trimesh.creation.cylinder(radius=0.008, height=0.80, sections=12)
    roller_parts = []
    roller_count = int(CONVEYOR_LENGTH / roller_pitch)
    for index in range(roller_count):
        roller_y = CONVEYOR_Y_MIN + 0.05 + index * roller_pitch
        seat = transform((0.0, roller_y, deck_top - roller_radius)) @ lie_along_x
        roller_parts.append((roller, seat, MAT_STEEL))
        roller_parts.append((journal, seat, MAT_DARK_METAL))
    # Split into sections so no single mesh spans the whole bay.
    for start in range(0, len(roller_parts), 120):
        scene.add(assembly_mesh(roller_parts[start : start + 120]))
    scene.add(
        box_mesh((0.66, CONVEYOR_LENGTH + 0.35, 0.022), MAT_BLACK),
        pose=transform((0.0, CONVEYOR_CENTER_Y, deck_top - 0.085)),
    )
    frame_parts = []
    for x in (-0.42, 0.42):
        frame_parts.extend(
            extrusion_parts(
                (0.10, 0.18),
                CONVEYOR_LENGTH + 0.50,
                transform((x, CONVEYOR_CENTER_Y, 0.30), rpy=(math.pi / 2.0, 0.0, 0.0)),
            )
        )
        frame_parts.append(
            (
                chamfer_box((0.116, CONVEYOR_LENGTH + 0.50, 0.012), 0.004),
                transform((x, CONVEYOR_CENTER_Y, 0.395)),
                MAT_BRUSHED,
            )
        )
    scene.add(assembly_mesh(frame_parts))
    # Product guide rails on posts clamped into the frame slot.
    for x in (-0.38, 0.38):
        rail_parts = [
            (
                chamfer_cylinder(0.016, CONVEYOR_LENGTH + 0.35, sections=16),
                transform((x, CONVEYOR_CENTER_Y, 0.645), rpy=(math.pi / 2, 0, 0)),
                MAT_ALUMINUM,
            )
        ]
        for y in np.linspace(CONVEYOR_Y_MIN + 0.35, CONVEYOR_Y_MAX - 0.35, 22):
            rail_parts.append(
                (
                    chamfer_box((0.030, 0.040, 0.24), 0.004),
                    transform((x, y, 0.515)),
                    MAT_ALUMINUM,
                )
            )
            rail_parts.append(
                (
                    chamfer_box((0.052, 0.052, 0.030), 0.006),
                    transform((x, y, 0.645)),
                    MAT_BRUSHED,
                )
            )
            rail_parts.append(
                (
                    hex_bolt(0.014, 0.009),
                    transform(
                        (x - math.copysign(0.030, x), y, 0.645),
                        rpy=(0.0, -math.copysign(math.pi / 2.0, x), 0.0),
                    ),
                    MAT_STEEL,
                )
            )
            rail_parts.append(
                (
                    hex_bolt(0.014, 0.009),
                    transform(
                        (x - math.copysign(0.026, x), y, 0.408),
                        rpy=(0.0, -math.copysign(math.pi / 2.0, x), 0.0),
                    ),
                    MAT_STEEL,
                )
            )
        scene.add(assembly_mesh(rail_parts))
    for y in np.linspace(CONVEYOR_Y_MIN + 0.45, CONVEYOR_Y_MAX - 0.45, 16):
        stand_parts = list(
            extrusion_parts(
                0.065,
                0.90,
                transform((0.0, y, 0.235), rpy=(0.0, math.pi / 2.0, 0.0)),
            )
        )
        for x in (-0.43, 0.43):
            stand_parts.extend(extrusion_parts(0.065, 0.21, transform((x, y, 0.155))))
            stand_parts.extend(levelling_foot_parts(transform((x, y, 0.0))))
            # Gusset between leg and cross member.
            stand_parts.append(
                (
                    chamfer_box((0.075, 0.010, 0.075), 0.003),
                    transform(
                        (
                            x - math.copysign(0.062, x),
                            y - 0.040,
                            0.203,
                        ),
                        rpy=(0.0, math.copysign(math.pi / 4.0, x), 0.0),
                    ),
                    MAT_BRUSHED,
                )
            )
        scene.add(assembly_mesh(stand_parts))
    # End pulley housings.
    for y in (CONVEYOR_Y_MIN - 0.35, CONVEYOR_Y_MAX + 0.35):
        end_parts = [
            (chamfer_box((0.90, 0.12, 0.22), 0.008), transform((0.0, y, 0.31)), MAT_ALUMINUM),
            (
                chamfer_cylinder(0.055, 0.62, sections=24),
                transform((0.0, y, deck_top - 0.055)) @ lie_along_x,
                MAT_BRUSHED,
            ),
        ]
        for x in (-0.34, 0.34):
            end_parts.extend(
                bolt_circle_parts(
                    4,
                    0.028,
                    0.013,
                    0.008,
                    transform(
                        (x, y - math.copysign(0.062, y), deck_top - 0.055),
                        rpy=(-math.pi / 2.0 if y > 0 else math.pi / 2.0, 0.0, 0.0),
                    ),
                )
            )
        scene.add(assembly_mesh(end_parts))

    # Twenty identical carriers fill the belt at a constant pitch. Product
    # detail is revealed by world position after each station, so upstream
    # parts arrive continuously and the loop boundary is spatially seamless.
    pallet_mesh = pallet_assembly_mesh()
    junction_box_mesh = housing_assembly_mesh()
    open_tray_mesh = busbar_tray_mesh()
    cover_mesh = cover_assembly_mesh()
    port_mesh = cable_gland_mesh()
    port_face_mesh = box_mesh((0.014, 0.050, 0.044), MAT_DARK_METAL)
    connector_mesh = hv_connector_mesh()
    static_cable_mesh = cylinder_mesh(0.014, 0.60, MAT_HV_ORANGE, sections=28)
    branch_cable_mesh = cylinder_mesh(0.012, 0.34, MAT_HV_ORANGE, sections=28)
    clip_mesh = cable_clip_mesh()
    strain_mesh = strain_relief_mesh()
    latch_mesh = toggle_latch_mesh()
    terminal_mesh = terminal_stud_mesh()

    def add_item(mesh, offset, local_pose, required_stage):
        conveyor_items.append(
            ConveyorItem(
                scene.add(mesh, pose=np.eye(4)),
                offset,
                local_pose,
                required_stage,
            )
        )

    def add_product(offset):
        add_item(
            pallet_mesh,
            offset,
            transform((0.0, 0.0, 0.425)),
            0,
        )
        add_item(
            junction_box_mesh,
            offset,
            transform((0.0, 0.0, 0.505)),
            1,
        )
        add_item(
            open_tray_mesh,
            offset,
            transform((0.0, 0.0, 0.576)),
            1,
        )
        for port_x in (-0.268, 0.268):
            for port_y in (-0.30, 0.30):
                add_item(
                    port_mesh,
                    offset,
                    transform((port_x, port_y, 0.625)),
                    1,
                )
                add_item(
                    port_face_mesh,
                    offset,
                    transform(
                        (
                            port_x + math.copysign(0.039, port_x),
                            port_y,
                            0.625,
                        )
                    ),
                    1,
                )
        for port_y in (-0.30, 0.30):
            add_item(
                connector_mesh,
                offset,
                transform((0.28, port_y, 0.650)),
                2,
            )
        add_item(
            static_cable_mesh,
            offset,
            transform(
                (0.345, 0.0, 0.650),
                rpy=(math.pi / 2, 0.0, 0.0),
            ),
            2,
        )
        add_item(
            static_cable_mesh,
            offset,
            transform(
                (-0.06, 0.0, 0.622),
                rpy=(math.pi / 2, 0.0, 0.0),
            ),
            3,
        )
        add_item(
            branch_cable_mesh,
            offset,
            transform(
                (0.08, 0.0, 0.632),
                rpy=(0.0, math.pi / 2, 0.0),
            ),
            4,
        )
        for clip_y in (-0.20, 0.20):
            add_item(
                clip_mesh,
                offset,
                transform((0.0, clip_y, 0.650)),
                5,
            )
        add_item(
            strain_mesh,
            offset,
            transform((0.0, 0.0, 0.675)),
            6,
        )
        add_item(
            cover_mesh,
            offset,
            transform((0.0, 0.0, 0.704)),
            7,
        )
        for latch_y in (-0.22, 0.22):
            add_item(
                latch_mesh,
                offset,
                transform((-0.05, latch_y, 0.735)),
                8,
            )
        for terminal_y in (-0.24, 0.24):
            add_item(
                terminal_mesh,
                offset,
                transform(
                    (0.02, terminal_y, 0.738),
                    rpy=(0.0, math.pi / 2, 0.0),
                ),
                9,
            )

    for panel_index in range(PANEL_COUNT):
        add_product((PANEL_BASE_OFFSET + PANEL_PITCH * panel_index) % CONVEYOR_LENGTH)

    for cell_index, (cx, cy, _) in enumerate(CELL_LAYOUT):
        rotating_nodes.extend(add_assembly_cell(scene, cell_index, (cx, cy)))
        if not fetches_component(cell_index):
            # Test and inspection stations have no components to present.
            continue
        add_stocker(scene, cell_index, cx, cy)

    for cell_index, (cx, cy, _) in enumerate(CELL_LAYOUT):
        add_station_hardware(scene, dynamic_nodes, cell_index, cx, cy)
    add_line_services(scene)
    add_infeed_outfeed(scene)
    add_ceiling(scene)
    add_line_lighting(scene)
    return rotating_nodes, conveyor_items, dynamic_nodes


FLOOR_WIDTH = 26.0
FLOOR_DEPTH = 56.0
FLOOR_CENTER_Y = 6.0
FLOOR_PPM = 46
WALK_INNER_X = 3.55
WALK_OUTER_X = 4.95
# Placards hang over the walkway, clear of the line itself.
SIGN_X = 4.25
SIGN_RAIL_Z = 3.42
CEILING_HEIGHT = 7.20
TRUSS_LOWER = 5.90
TRUSS_UPPER = 6.55
LIGHT_HEIGHT = 3.30
BAY_Y_MIN = -24.0
BAY_Y_MAX = 14.0
LIGHT_Y_MIN = -18.6
LIGHT_Y_MAX = 12.6
# One full orbit per film. The camera flies inside the column line, above the
# suspended rails and below the roof steel, so it never passes through the
# building; a constant angular rate keeps the move as loop-clean as the line.
ORBIT_CENTRE = (0.0, 1.20)
ORBIT_RADIUS = 9.60
ORBIT_HEIGHT = 4.80
ORBIT_HEIGHT_SWING = 0.40
ORBIT_TARGET_Z = 1.80
ORBIT_START_ANGLE = math.radians(31.5)
CAMERA_MODE = "orbit"
MONOCHROME = True
# Set by --eye/--target to park the camera anywhere for a close look.
INSPECT_VIEW = None
# The control panel stands beyond the walkway so it never blocks the line.
CABINET_X = 5.55
CABINET_Y = 1.20
# The monitoring desk stands opposite the control panel and clear of the
# walkway, turned so the screens face back across the line: that is the only
# heading the orbit ever sees them from — from the near side the camera is
# directly overhead and the desk falls below the frame.
STATION_CENTRE = (6.45, 1.20)
STATION_YAW = math.radians(180.0)
# Barrier line, between the stockers (out to 2.25 m) and the operator panels
# (at 3.25 m), with one opening per side onto the line.
BARRIER_X = 2.72
BARRIER_HEIGHT = 1.10
BARRIER_Y_MIN = CELL_Y_START - 1.40
BARRIER_Y_MAX = CELL_Y_START + 9.0 * CELL_Y_SPACING + 1.40
BARRIER_GATE_Y = CELL_Y_START + 4.0 * CELL_Y_SPACING
BARRIER_GATE_WIDTH = 1.10
# Take-off robot: pedestal, the point it lifts from and the slot it fills.
PALLETISER_BASE = (1.20, 8.85, 0.80)
PALLETISER_PICK = (0.28, 8.85, 0.545)
PALLETISER_PLACE = (2.20, 8.51, 1.045)
# Shelf spacing has to clear a three-high stack of 0.10 m units plus the
# shelf plate, or the top of one stack grows through the shelf above it.
STOCKER_SHELVES = (0.22, 0.60, 0.98)
FOG_COLOUR = np.array((0.325, 0.352, 0.362), dtype=np.float32)
FOG_START = 16.0
FOG_RANGE = 34.0
FOG_MAX = 0.72
FONT_CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
PAINT_YELLOW = (216, 160, 28)
PAINT_WHITE = (204, 208, 203)
PAINT_JOINT = (88, 93, 93)
STATION_LABELS = tuple(f"OP{(index + 1) * 10:03d}" for index in range(10))
STATION_NAMES = (
    "HOUSING LOAD",
    "HV CONNECTOR",
    "MAIN ROUTE",
    "BRANCH ROUTE",
    "CLIP SEAT",
    "STRAIN RELIEF",
    "COVER PLACE",
    "LATCH PRESS",
    "E-TEST",
    "VISION",
)


def floor_pixel(x, y):
    return (
        (x + FLOOR_WIDTH / 2.0) * FLOOR_PPM,
        (FLOOR_CENTER_Y + FLOOR_DEPTH / 2.0 - y) * FLOOR_PPM,
    )


def _paint_rect(draw, x0, y0, x1, y1, colour):
    left, top = floor_pixel(min(x0, x1), max(y0, y1))
    right, bottom = floor_pixel(max(x0, x1), min(y0, y1))
    draw.rectangle((left, top, right, bottom), fill=colour)


def _paint_outline(draw, x0, y0, x1, y1, colour, stroke=0.06):
    half = stroke / 2.0
    _paint_rect(draw, x0 - half, y0 - half, x1 + half, y0 + half, colour)
    _paint_rect(draw, x0 - half, y1 - half, x1 + half, y1 + half, colour)
    _paint_rect(draw, x0 - half, y0, x0 + half, y1, colour)
    _paint_rect(draw, x1 - half, y0, x1 + half, y1, colour)


def _paint_hatch(image, x0, y0, x1, y1, colour, pitch=0.22):
    left, top = floor_pixel(min(x0, x1), max(y0, y1))
    right, bottom = floor_pixel(max(x0, x1), min(y0, y1))
    box = (int(left), int(top), int(right), int(bottom))
    width, height = box[2] - box[0], box[3] - box[1]
    if width <= 2 or height <= 2:
        return
    patch = Image.new("RGB", (width, height), (54, 57, 57))
    stripe = ImageDraw.Draw(patch)
    step = max(3, int(pitch * FLOOR_PPM))
    for offset in range(-height, width + height, step * 2):
        stripe.line((offset, height, offset + height, 0), fill=colour, width=step)
    image.paste(patch, box)


def _paint_text(
    image,
    text,
    x,
    y,
    size,
    colour,
    font_path=FONT_SANS,
    font_index=0,
    angle=0.0,
):
    pixels = max(8, int(size * FLOOR_PPM))
    font = ImageFont.truetype(font_path, pixels, index=font_index)
    layer = Image.new(
        "RGBA",
        (pixels * (len(text) + 3), int(pixels * 2.2)),
        (0, 0, 0, 0),
    )
    ImageDraw.Draw(layer).text((pixels // 2, pixels // 2), text, font=font, fill=colour + (255,))
    bounds = layer.getbbox()
    if bounds is None:
        return
    layer = layer.crop(bounds)
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    center_x, center_y = floor_pixel(x, y)
    image.paste(
        layer,
        (
            int(center_x - layer.width / 2.0),
            int(center_y - layer.height / 2.0),
        ),
        layer,
    )


def make_floor_texture():
    """Painted concrete: control joints, walkways and equipment footprints."""
    width = int(FLOOR_WIDTH * FLOOR_PPM)
    height = int(FLOOR_DEPTH * FLOOR_PPM)
    rng = np.random.default_rng(11)
    coarse = rng.normal(0.0, 1.0, (height // 26 + 2, width // 26 + 2))
    grain = np.asarray(
        Image.fromarray(np.uint8(np.clip(coarse * 15.0 + 168.0, 0, 255)), "L").resize((width, height), Image.BICUBIC),
        dtype=np.float32,
    )
    speckle = rng.normal(0.0, 3.4, (height, width)).astype(np.float32)
    base = np.stack(
        (
            grain * 0.97 + speckle,
            grain * 1.00 + speckle,
            grain * 0.99 + speckle,
        ),
        axis=2,
    )
    image = Image.fromarray(np.uint8(np.clip(base, 0, 255)), "RGB").convert("RGB")
    draw = ImageDraw.Draw(image)

    # Saw-cut control joints on a 3 m grid.
    for x in np.arange(-12.0, 12.1, 3.0):
        _paint_rect(draw, x - 0.012, -22.0, x + 0.012, 34.0, PAINT_JOINT)
    for y in np.arange(-21.0, 34.0, 3.0):
        _paint_rect(draw, -13.0, y - 0.012, 13.0, y + 0.012, PAINT_JOINT)

    # Safety walkways down both sides of the cell.
    for side in (-1.0, 1.0):
        for edge in (WALK_INNER_X, WALK_OUTER_X):
            _paint_rect(
                draw,
                side * edge - 0.05,
                -16.5,
                side * edge + 0.05,
                12.6,
                PAINT_YELLOW,
            )
        # Floor lettering is laid out for someone walking the line towards the
        # infeed, which is also the direction the camera looks.
        for label_y in (2.6, -8.4):
            _paint_text(
                image,
                "安全通路",
                side * (WALK_INNER_X + WALK_OUTER_X) / 2.0,
                label_y,
                0.52,
                PAINT_YELLOW,
                font_path=FONT_CJK,
                angle=180.0,
            )

    # Footprint of every cell, its stocker and its control box.
    for cell_index, (cx, cy, _) in enumerate(CELL_LAYOUT):
        side = -1.0 if cx < 0 else 1.0
        _paint_outline(
            draw,
            side * 0.50,
            cy - 0.62,
            side * (STOCKER_OUTER_X + 0.20 if fetches_component(cell_index) else STOCKER_OUTER_X - 0.05),
            cy + 0.62,
            PAINT_YELLOW,
            stroke=0.05,
        )
        _paint_text(
            image,
            STATION_LABELS[cell_index],
            side * (WALK_INNER_X - 0.62),
            cy + 0.02,
            0.34,
            PAINT_WHITE,
            angle=180.0,
        )

    # Keep-clear zone in front of the line control panel.
    _paint_hatch(
        image,
        -(CABINET_X - 1.05),
        CABINET_Y - 0.90,
        -(CABINET_X - 0.30),
        CABINET_Y + 0.90,
        PAINT_YELLOW,
    )

    # Transfer ends of the line.
    _paint_hatch(image, -2.2, -8.5, 2.2, -7.4, PAINT_YELLOW, pitch=0.26)
    _paint_text(image, "PALLET INFEED", 0.0, -9.35, 0.40, PAINT_WHITE, angle=180.0)
    _paint_hatch(image, -2.2, 7.5, 2.2, 8.6, PAINT_YELLOW, pitch=0.26)
    return image


def make_sign_texture(label, name, width=384, height=128):
    image = Image.new("RGB", (width, height), (18, 34, 62))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width - 1, height - 1), outline=(150, 158, 165), width=4)
    draw.rectangle((0, 0, width - 1, 8), fill=(150, 158, 165))
    draw.text(
        (18, 16),
        label,
        font=ImageFont.truetype(FONT_SANS, 54),
        fill=(238, 242, 245),
    )
    draw.text(
        (18, 82),
        name,
        font=ImageFont.truetype(FONT_SANS, 30),
        fill=(150, 190, 225),
    )
    return image


def make_andon_texture(width=1280, height=596):
    """A shop-floor production board: one column per station, five rows."""
    image = Image.new("RGB", (width, height), (16, 17, 19))
    draw = ImageDraw.Draw(image)
    frame = 12
    draw.rectangle(
        (frame, frame, width - frame - 1, height - frame - 1),
        outline=(126, 132, 138),
        width=3,
    )

    title_font = ImageFont.truetype(FONT_CJK, 36, index=0)
    banner_font = ImageFont.truetype(FONT_CJK, 32, index=0)
    label_font = ImageFont.truetype(FONT_CJK, 27, index=0)
    head_font = ImageFont.truetype(FONT_SANS, 25)
    value_font = ImageFont.truetype(FONT_MONO, 27)

    left = frame + 10
    right = width - frame - 11
    top = frame + 10
    title_h = 60
    draw.rectangle((left, top, right, top + title_h), fill=(236, 238, 236))
    draw.text(
        (left + 16, top + 10),
        "EVジャンクションボックス組立ライン 生産管理板",
        font=title_font,
        fill=(16, 18, 20),
    )
    banner_w = 316
    draw.rectangle((right - banner_w, top, right, top + title_h), fill=(20, 128, 58))
    draw.text(
        (right - banner_w + 26, top + 12),
        "全工程 運転中",
        font=banner_font,
        fill=(240, 248, 240),
    )

    table_top = top + title_h + 12
    table_bottom = height - frame - 12
    rows = ("工程", "品番", "目標数", "実績数", "可動率", "サイクル")
    row_h = (table_bottom - table_top) / len(rows)
    label_w = 156
    column_w = (right - left - label_w) / len(STATION_LABELS)

    rng = np.random.default_rng(5)
    target = 4380
    actual = target - rng.integers(0, 22, size=len(STATION_LABELS))
    uptime = 100.0 - rng.random(len(STATION_LABELS)) * 1.7
    takt = CYCLE_TIME + (rng.random(len(STATION_LABELS)) - 0.5) * 0.12

    for row_index, row_label in enumerate(rows):
        row_top = table_top + row_h * row_index
        row_low = row_top + row_h - 2
        draw.rectangle((left, row_top, left + label_w, row_low), fill=(238, 240, 238))
        draw.text(
            (left + 12, row_top + row_h * 0.5 - 16),
            row_label,
            font=label_font,
            fill=(16, 18, 20),
        )
        for column_index, station in enumerate(STATION_LABELS):
            cell_left = left + label_w + column_w * column_index
            cell_right = cell_left + column_w - 2
            if row_index == 0:
                fill = (86, 206, 222) if column_index % 2 == 0 else (232, 214, 74)
                draw.rectangle((cell_left, row_top, cell_right, row_low), fill=fill)
                draw.text(
                    (cell_left + 12, row_top + row_h * 0.5 - 15),
                    station,
                    font=head_font,
                    fill=(16, 18, 20),
                )
                continue
            text = {
                1: "JB-EV-2410",
                2: f"{target}",
                3: f"{actual[column_index]}",
                4: f"{uptime[column_index]:.1f}",
                5: f"{takt[column_index]:.2f}",
            }[row_index]
            font = value_font if row_index != 1 else head_font
            draw.rectangle((cell_left, row_top, cell_right, row_low), fill=(244, 245, 243))
            span = draw.textlength(text, font=font)
            draw.text(
                (
                    cell_left + (column_w - 2 - span) / 2.0,
                    row_top + row_h * 0.5 - 16,
                ),
                text,
                font=font,
                fill=(20, 22, 24),
            )
    return image


def _screen_curve(draw, box, values, colour, width=3):
    x0, y0, x1, y1 = box
    low, high = float(values.min()), float(values.max())
    span = max(high - low, 1e-6)
    count = len(values)
    points = [
        (
            x0 + (x1 - x0) * index / (count - 1),
            y1 - (y1 - y0) * (values[index] - low) / span,
        )
        for index in range(count)
    ]
    draw.line(points, fill=colour, width=width, joint="curve")


def _screen_frame(draw, box, colour=(52, 58, 62), rows=4, columns=6):
    x0, y0, x1, y1 = box
    draw.rectangle(box, outline=colour, width=2)
    for index in range(1, columns):
        x = x0 + (x1 - x0) * index / columns
        draw.line((x, y0, x, y1), fill=colour, width=1)
    for index in range(1, rows):
        y = y0 + (y1 - y0) * index / rows
        draw.line((x0, y, x1, y), fill=colour, width=1)


def make_training_screen_texture(kind, width=1024, height=576):
    """What the line's own training run looks like on a monitor.

    Three panes of one workstation: the run itself, the policy being trained,
    and the cell the camera is watching. Dark ground, bright ink — the film is
    graded to black and white, so these have to carry on contrast alone.
    """
    ink = (222, 230, 232)
    dim = (128, 138, 142)
    accent = (236, 152, 48)
    line = (96, 206, 158)
    image = Image.new("RGB", (width, height), (12, 14, 16))
    draw = ImageDraw.Draw(image)
    head = ImageFont.truetype(FONT_MONO, 19)
    small = ImageFont.truetype(FONT_MONO, 15)
    tiny = ImageFont.truetype(FONT_MONO, 13)
    big = ImageFont.truetype(FONT_MONO, 34)
    rng = np.random.default_rng({"run": 11, "policy": 23, "cell": 37}[kind])

    draw.rectangle((0, 0, width - 1, 34), fill=(24, 27, 30))
    title = {
        "run": "TRAINING RUN  ur15-line-assy  ep 41,208",
        "policy": "POLICY  sac-mlp-1024  step 8.42M",
        "cell": "CELL OP070  vision + force",
    }[kind]
    draw.text((14, 9), title, font=head, fill=ink)
    draw.text((width - 132, 9), "● LIVE", font=head, fill=line)

    if kind == "run":
        # Return per episode, still climbing, with the running mean over it.
        steps = np.linspace(0.0, 1.0, 320)
        reward = 1.0 - np.exp(-3.4 * steps)
        noisy = reward + rng.normal(0.0, 0.055, steps.size) * (1.1 - steps)
        # Pad before smoothing, or the running mean dives at both ends and
        # the run looks like it collapsed on its last episode.
        window = 18
        padded = np.concatenate(
            (
                np.full(window, noisy[0]),
                noisy,
                np.full(window, noisy[-1]),
            )
        )
        smooth = np.convolve(padded, np.ones(window) / window, mode="same")[window:-window]
        plot = (60, 74, width - 30, 330)
        _screen_frame(draw, plot)
        _screen_curve(draw, plot, noisy, dim, 2)
        _screen_curve(draw, plot, smooth, line, 4)
        draw.text((66, 46), "EPISODE RETURN", font=small, fill=dim)
        for index, label in enumerate(("1.0", "0.5", "0.0")):
            draw.text((22, 66 + index * 128), label, font=tiny, fill=dim)
        cells = (
            ("RETURN", "0.912"),
            ("SUCCESS", "98.4%"),
            ("CYCLE", "26.27s"),
            ("KL", "0.0041"),
        )
        for index, (label, value) in enumerate(cells):
            box_x = 60 + index * ((width - 90) / 4)
            draw.rectangle(
                (box_x, 360, box_x + (width - 90) / 4 - 14, 452),
                outline=(52, 58, 62),
                width=2,
            )
            draw.text((box_x + 14, 372), label, font=tiny, fill=dim)
            draw.text((box_x + 14, 396), value, font=big, fill=ink)
        for index in range(4):
            draw.text(
                (60, 476 + index * 22),
                f"ep {41204 + index}  return {0.87 + index * 0.014:.3f}  steps {412 + index * 3}  ok",
                font=tiny,
                fill=dim if index else ink,
            )
    elif kind == "policy":
        # Loss falling, entropy settling, and the gripper's own traces.
        steps = np.linspace(0.0, 1.0, 300)
        loss = np.exp(-2.8 * steps) + rng.normal(0.0, 0.02, steps.size) * (1.0 - steps * 0.6)
        entropy = 0.4 + 0.5 * np.exp(-4.0 * steps) + rng.normal(0.0, 0.012, steps.size)
        upper = (60, 66, width - 30, 240)
        lower = (60, 288, width - 30, 452)
        _screen_frame(draw, upper, rows=3)
        _screen_curve(draw, upper, loss, accent, 3)
        draw.text((66, 44), "CRITIC LOSS", font=small, fill=dim)
        _screen_frame(draw, lower, rows=3)
        _screen_curve(draw, lower, entropy, line, 3)
        draw.text((66, 266), "POLICY ENTROPY", font=small, fill=dim)
        for index, text in enumerate(
            (
                "lr 3.0e-4   batch 1024   buffer 2.0M",
                "grad norm 0.87   clip 1.0   tau 0.005",
                "reward  seat 0.42  align 0.31  time 0.27",
            )
        ):
            draw.text((60, 486 + index * 24), text, font=tiny, fill=dim)
    else:
        # The station's own stereo view, with what it is tracking.
        view = (36, 66, 612, 452)
        draw.rectangle(view, fill=(26, 30, 32), outline=(52, 58, 62), width=2)
        for index in range(1, 8):
            x = view[0] + (view[2] - view[0]) * index / 8
            draw.line((x, view[1], x, view[3]), fill=(38, 43, 46), width=1)
        for index in range(1, 6):
            y = view[1] + (view[3] - view[1]) * index / 6
            draw.line((view[0], y, view[2], y), fill=(38, 43, 46), width=1)
        # What the head is actually looking at: a clamped pallet seen from
        # above and in front, so the detections have something to sit on.
        draw.polygon(
            ((104, 386), (196, 128), (486, 128), (566, 386)),
            fill=(58, 64, 68),
            outline=(88, 96, 100),
        )
        draw.polygon(
            ((150, 268), (206, 150), (446, 150), (498, 268)),
            fill=(92, 100, 104),
            outline=(126, 136, 140),
        )
        draw.polygon(
            ((196, 244), (232, 168), (420, 168), (452, 244)),
            fill=(34, 38, 40),
        )
        draw.rectangle((372, 196, 470, 262), fill=(150, 96, 40))
        draw.rectangle((196, 300, 292, 360), fill=(64, 92, 120))
        for box, label in (
            ((150, 150, 356, 268), "housing 0.99"),
            ((372, 196, 470, 262), "cover 0.97"),
            ((196, 300, 292, 360), "clip 0.94"),
        ):
            draw.rectangle(box, outline=line, width=3)
            draw.text((box[0], box[1] - 20), label, font=tiny, fill=line)
        draw.text((44, 44), "STEREO 1280x720  30fps", font=small, fill=dim)
        panel_x = 636
        draw.text((panel_x, 44), "FORCE / TORQUE", font=small, fill=dim)
        for index, (label, value) in enumerate(
            (
                ("Fx", "  2.1 N"),
                ("Fy", " -0.8 N"),
                ("Fz", " 18.4 N"),
                ("Tx", " 0.11 Nm"),
                ("Ty", "-0.04 Nm"),
                ("Tz", " 0.02 Nm"),
            )
        ):
            row_y = 74 + index * 34
            draw.text((panel_x, row_y), label, font=small, fill=dim)
            draw.text((panel_x + 46, row_y), value, font=small, fill=ink)
            bar = min(abs(float(value.split()[0])) / 20.0, 1.0)
            draw.rectangle(
                (panel_x + 150, row_y + 6, panel_x + 150 + bar * 210, row_y + 16),
                fill=accent if index == 2 else (72, 90, 96),
            )
        draw.text((panel_x, 300), "GRIP", font=small, fill=dim)
        draw.rectangle((panel_x, 326, width - 36, 356), outline=(52, 58, 62), width=2)
        draw.rectangle((panel_x + 3, 329, panel_x + 232, 353), fill=line)
        draw.text((panel_x, 386), "SEATED  OK", font=head, fill=line)
        draw.text((panel_x, 420), "residual 0.4 mm", font=small, fill=dim)
        # Cycle timeline along the bottom, with the dwell marked out.
        draw.text((36, 476), "CYCLE", font=small, fill=dim)
        bar = (110, 480, width - 36, 502)
        draw.rectangle(bar, outline=(52, 58, 62), width=2)
        draw.rectangle(
            (bar[0] + 2, bar[1] + 2, bar[0] + (bar[2] - bar[0]) * 0.50, bar[3] - 2),
            fill=(60, 74, 80),
        )
        draw.rectangle(
            (
                bar[0] + (bar[2] - bar[0]) * 0.55,
                bar[1] + 2,
                bar[0] + (bar[2] - bar[0]) * 0.86,
                bar[3] - 2,
            ),
            fill=line,
        )
        for label, position in (
            ("index", 0.24),
            ("clamp", 0.52),
            ("work", 0.70),
            ("release", 0.92),
        ):
            draw.text(
                (bar[0] + (bar[2] - bar[0]) * position - 22, 510),
                label,
                font=tiny,
                fill=dim,
            )
    return image


def make_operator_panel_texture(width=640, height=392):
    """Machine control panel: e-stop, selectors, jog dial and key blocks."""
    image = Image.new("RGB", (width, height), (26, 27, 29))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width - 1, height - 1), outline=(58, 60, 64), width=6)
    key = (44, 46, 50)
    key_edge = (18, 19, 21)
    for accent_y in (104, 232):
        draw.line((26, accent_y, width - 26, accent_y), fill=(196, 104, 26), width=3)

    def button(x, y, size, fill=key, radius=6):
        draw.rounded_rectangle(
            (x, y, x + size, y + size),
            radius=radius,
            fill=fill,
            outline=key_edge,
            width=2,
        )

    def dial(x, y, radius, face=(34, 35, 38)):
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=face,
            outline=(16, 17, 18),
            width=3,
        )

    # Emergency stop, mode selectors and the jog dial on the left.
    draw.ellipse((30, 26, 100, 96), fill=(24, 24, 26), outline=(12, 12, 13), width=3)
    draw.ellipse((38, 34, 92, 88), fill=(176, 26, 20), outline=(120, 14, 10), width=3)
    draw.ellipse((52, 46, 78, 66), fill=(206, 60, 48))
    for switch_x in (128, 196):
        dial(switch_x, 60, 26)
        draw.line((switch_x, 60, switch_x + 18, 42), fill=(196, 104, 26), width=5)
    dial(86, 176, 52)
    dial(86, 176, 18, face=(20, 21, 23))
    draw.line((86, 176, 118, 148), fill=(196, 104, 26), width=6)
    dial(176, 168, 30)
    draw.ellipse((34, 250, 74, 290), fill=(206, 176, 34), outline=(120, 100, 16), width=3)
    for index in range(3):
        dial(112 + index * 46, 270, 19)

    # Axis pad and function keys in the middle.
    for row in range(3):
        for column in range(3):
            if row == 1 and column == 1:
                dial(300 + column * 54, 44 + row * 46, 22)
            else:
                dial(300 + column * 54, 44 + row * 46, 20)
    for row in range(2):
        for column in range(4):
            button(286 + column * 46, 150 + row * 44, 34)

    # Key block on the right.
    for row in range(4):
        for column in range(4):
            button(478 + column * 38, 30 + row * 38, 30, radius=5)

    # Wide keys and indicators along the bottom.
    for column in range(9):
        button(30 + column * 44, 252, 36)
        button(30 + column * 44, 300, 36)
    for index, tint in enumerate(((60, 132, 214), (60, 132, 214), (208, 118, 30), (74, 186, 96))):
        draw.ellipse((470 + index * 30, 300, 486 + index * 30, 316), fill=tint)
    for column in range(2):
        dial(494 + column * 62, 262, 24)
    draw.rounded_rectangle((560, 292, 610, 330), radius=6, fill=(52, 54, 58), outline=key_edge, width=2)
    return image


def make_control_cabinet_texture(width=640, height=840):
    """Front of the line control panel: HMI, lamp row, switches, buttons."""
    body = (206, 208, 205)
    trim = (28, 29, 31)
    image = Image.new("RGB", (width, height), body)
    draw = ImageDraw.Draw(image)
    seam = width // 2
    draw.rectangle((0, 0, width - 1, height - 1), outline=trim, width=7)
    draw.line((seam, 8, seam, height - 9), fill=(150, 152, 150), width=5)

    title_font = ImageFont.truetype(FONT_SANS, 26)
    small_font = ImageFont.truetype(FONT_SANS, 18)
    jp_font = ImageFont.truetype(FONT_CJK, 22, index=0)

    # Nameplate across the top of the left door.
    draw.rectangle((30, 34, seam - 30, 84), fill=trim)
    draw.text((46, 44), "LINE 1  CONTROL PANEL", font=title_font, fill=(228, 230, 228))

    # HMI in a dark bezel.
    draw.rectangle((36, 106, seam - 36, 300), fill=trim)
    draw.rectangle((54, 124, seam - 54, 274), fill=(96, 122, 132))
    for row in range(4):
        draw.rectangle(
            (66, 136 + row * 34, seam - 66, 160 + row * 34),
            fill=(126, 150, 158),
            outline=(58, 74, 82),
            width=2,
        )
    draw.text((60, 280), "HMI", font=small_font, fill=(190, 194, 190))

    # Indicator lamps and selector switches.
    lamp_tints = (
        (86, 196, 104),
        (86, 196, 104),
        (226, 176, 52),
        (86, 196, 104),
        (206, 74, 58),
        (86, 196, 104),
    )
    for index, tint in enumerate(lamp_tints):
        cx = 62 + index * 42
        draw.ellipse((cx - 17, 336, cx + 17, 370), fill=(34, 35, 37))
        draw.ellipse((cx - 13, 340, cx + 13, 366), fill=tint)
        draw.ellipse((cx - 19, 404, cx + 19, 442), fill=(34, 35, 37))
        draw.line((cx, 423, cx + 12, 408), fill=(198, 106, 28), width=5)
        draw.rectangle((cx - 22, 452, cx + 22, 468), fill=(238, 240, 238), outline=trim)
    draw.text((36, 492), "運転 / 段取 / 保全", font=jp_font, fill=(52, 54, 56))

    # Right door: control buttons, lock and louvres.
    draw.ellipse((seam + 54, 120, seam + 118, 184), fill=(38, 40, 42))
    draw.ellipse((seam + 60, 126, seam + 112, 178), fill=(72, 168, 92))
    draw.ellipse((seam + 158, 120, seam + 222, 184), fill=(38, 40, 42))
    draw.ellipse((seam + 164, 126, seam + 216, 178), fill=(188, 48, 40))
    draw.text((seam + 54, 196), "START", font=small_font, fill=(52, 54, 56))
    draw.text((seam + 158, 196), "STOP", font=small_font, fill=(52, 54, 56))
    for row in range(3):
        for column in range(3):
            x0 = seam + 54 + column * 62
            y0 = 250 + row * 56
            draw.rounded_rectangle(
                (x0, y0, x0 + 44, y0 + 40),
                radius=5,
                fill=(232, 234, 232),
                outline=trim,
                width=2,
            )
    draw.rectangle((seam + 44, 452, width - 44, 470), fill=(150, 152, 150))
    draw.ellipse((width - 74, 500, width - 44, 530), fill=(126, 128, 126), outline=trim, width=2)
    for row in range(9):
        draw.rectangle(
            (seam + 60, 620 + row * 18, width - 60, 628 + row * 18),
            fill=(168, 170, 168),
        )
    draw.rectangle((40, 620, seam - 40, 780), outline=(150, 152, 150), width=4)
    draw.text((54, 800), "RLR-EV-JB-LINE-01", font=small_font, fill=(96, 98, 96))
    return image


def add_control_cabinet(scene, cabinet_x, cabinet_y, facing):
    """One line control panel, doors towards the walkway."""
    width, depth, tall = 1.62, 0.56, 2.08
    face_x = cabinet_x + facing * (depth / 2.0 + 0.006)
    parts = [
        (
            chamfer_box((depth + 0.06, width + 0.06, 0.12), 0.010),
            transform((cabinet_x, cabinet_y, 0.06)),
            MAT_CABINET_TRIM,
        ),
        (
            chamfer_box((depth, width, tall), 0.014),
            transform((cabinet_x, cabinet_y, 0.12 + tall / 2.0)),
            MAT_CABINET,
        ),
        (
            chamfer_box((depth + 0.08, width + 0.08, 0.07), 0.010),
            transform((cabinet_x, cabinet_y, 0.12 + tall)),
            MAT_CABINET_TRIM,
        ),
        # Cable entry and the duct that feeds the line.
        (
            chamfer_box((0.20, 0.46, 0.16), 0.008),
            transform((cabinet_x - facing * 0.30, cabinet_y, 0.20)),
            MAT_CABINET_TRIM,
        ),
        (
            chamfer_box((0.13, 0.11, 0.34), 0.006),
            transform((cabinet_x - facing * 0.34, cabinet_y - 0.30, 0.36)),
            MAT_DUCT,
        ),
        # Seam between the two doors.
        (
            chamfer_box((0.010, 0.014, tall - 0.10), 0.003),
            transform((face_x + facing * 0.004, cabinet_y, 0.12 + tall / 2.0)),
            MAT_CABINET_TRIM,
        ),
    ]
    # Espagnolette handle with its lock barrel, on each door.
    for handle_offset in (-0.05, 0.05):
        parts.append(
            (
                chamfer_box((0.030, 0.045, 0.30), 0.006),
                transform(
                    (
                        cabinet_x + facing * (depth / 2.0 + 0.022),
                        cabinet_y + handle_offset,
                        0.12 + tall * 0.52,
                    )
                ),
                MAT_CABINET_TRIM,
            )
        )
        parts.append(
            (
                chamfer_box((0.055, 0.028, 0.075), 0.005),
                transform(
                    (
                        cabinet_x + facing * (depth / 2.0 + 0.034),
                        cabinet_y + handle_offset * 1.9,
                        0.12 + tall * 0.52,
                    )
                ),
                MAT_BRUSHED,
            )
        )
        parts.append(
            (
                chamfer_cylinder(0.011, 0.020, sections=18),
                transform(
                    (
                        cabinet_x + facing * (depth / 2.0 + 0.020),
                        cabinet_y + handle_offset,
                        0.12 + tall * 0.52 - 0.20,
                    ),
                    rpy=(0.0, facing * math.pi / 2.0, 0.0),
                ),
                MAT_BRUSHED,
            )
        )
    # Hinges down both outer edges.
    for hinge_y in (cabinet_y - width / 2.0 + 0.03, cabinet_y + width / 2.0 - 0.03):
        for hinge_z in (0.45, 1.15, 1.90):
            parts.append(
                (
                    chamfer_cylinder(0.017, 0.075, sections=18),
                    transform((cabinet_x + facing * (depth / 2.0 + 0.012), hinge_y, hinge_z)),
                    MAT_CABINET_TRIM,
                )
            )
    # Lifting eyes on the roof, and the filter fan on the side wall.
    for eye_y in (cabinet_y - 0.62, cabinet_y + 0.62):
        for eye_x in (cabinet_x - 0.18, cabinet_x + 0.18):
            parts.append(
                (
                    trimesh.creation.annulus(r_min=0.016, r_max=0.030, height=0.014, sections=20),
                    transform((eye_x, eye_y, 0.12 + tall + 0.045), rpy=(math.pi / 2.0, 0.0, 0.0)),
                    MAT_STEEL,
                )
            )
    fan_y = cabinet_y + width / 2.0 + 0.004
    parts.append(
        (
            chamfer_box((0.30, 0.020, 0.30), 0.006),
            transform((cabinet_x, fan_y, 1.30)),
            MAT_CABINET_TRIM,
        )
    )
    for louvre_z in np.linspace(1.19, 1.41, 7):
        parts.append(
            (
                chamfer_box((0.26, 0.012, 0.016), 0.003),
                transform((cabinet_x, fan_y + 0.010, louvre_z), rpy=(math.radians(20.0), 0.0, 0.0)),
                MAT_DARK_METAL,
            )
        )
    scene.add(assembly_mesh(parts))
    scene.add(
        panel_mesh(width - 0.04, tall - 0.10, make_control_cabinet_texture()),
        pose=transform((face_x, cabinet_y, 0.12 + tall / 2.0)) @ rotate_z(-facing * math.pi / 2.0),
    )


def add_operator_panel(scene, panel_x, panel_y, side):
    """Operator station on a pedestal, facing the walkway."""
    depth, width, height = 0.05, 0.35, 0.23
    centre_z = 1.14
    post = centre_z - height / 2.0
    face_x = panel_x + side * (depth / 2.0 + 0.005)
    parts = [
        (chamfer_box((0.24, 0.24, 0.030), 0.006), transform((panel_x, panel_y, 0.015)), MAT_STEEL),
        # The post reaches the underside of the box, whatever size that is.
        (
            chamfer_cylinder(0.042, post, sections=24),
            transform((panel_x, panel_y, post / 2.0)),
            MAT_BRUSHED,
        ),
        (
            chamfer_cylinder(0.055, 0.035, sections=24),
            transform((panel_x, panel_y, 0.048)),
            MAT_CABINET_TRIM,
        ),
        (fillet_box((depth, width, height), 0.010), transform((panel_x, panel_y, centre_z)), MAT_CABINET_TRIM),
        # Sun shade over the face and the swivel bracket under the box.
        (
            chamfer_box((0.055, width + 0.02, 0.014), 0.004),
            transform(
                (panel_x + side * 0.020, panel_y, centre_z + height / 2.0 + 0.010),
                rpy=(0.0, side * math.radians(12.0), 0.0),
            ),
            MAT_CABINET_TRIM,
        ),
        (
            chamfer_box((0.06, 0.10, 0.055), 0.006),
            transform((panel_x, panel_y, centre_z - height / 2.0 - 0.022)),
            MAT_BRUSHED,
        ),
    ]
    parts.extend(
        bolt_row_parts(
            [(panel_x + x, panel_y + y, 0.030) for x in (-0.088, 0.088) for y in (-0.088, 0.088)],
            0.018,
            0.011,
        )
    )
    # The emergency stop is a real mushroom over the one the artwork draws:
    # a flat picture of a button is the first thing that reads as a render.
    face_rotation = (0.0, side * math.pi / 2.0, 0.0)
    estop = (face_x + side * 0.002, panel_y - side * 0.1275, centre_z + 0.0689)
    parts.append(
        (
            chamfer_cylinder(0.021, 0.010, sections=26),
            transform(estop, rpy=face_rotation),
            MAT_SAFETY_YELLOW,
        )
    )
    parts.append(
        (
            chamfer_cylinder(0.017, 0.014, chamfer=0.004, sections=26),
            transform(
                (
                    estop[0] + side * 0.012,
                    estop[1],
                    estop[2],
                ),
                rpy=face_rotation,
            ),
            MAT_ESTOP_RED,
        )
    )
    scene.add(assembly_mesh(parts))
    scene.add(
        panel_mesh(width - 0.03, height - 0.03, make_operator_panel_texture()),
        pose=transform((face_x, panel_y, centre_z)) @ rotate_z(-side * math.pi / 2.0),
    )


def add_monitoring_station(scene, centre, yaw):
    """The desk the line is watched from: three screens, keyboard, chair.

    Built in its own frame — +X is the way the screens face, which is also
    where the chair goes, and Y runs along the desk — then dropped into the
    bay by one transform. Everything except the screens themselves is merged
    into a single mesh.
    """
    root = transform((centre[0], centre[1], 0.0)) @ rotate_z(yaw)
    desk_top = 0.745
    parts = [
        (
            chamfer_box((0.88, 2.10, 0.038), 0.006),
            transform((0.0, 0.0, desk_top - 0.019)),
            MAT_WHITE_SATIN,
        ),
        # Lower shelf and the tray that keeps the leads off the floor.
        (
            chamfer_box((0.70, 1.30, 0.020), 0.004),
            transform((0.0, 0.0, 0.20)),
            MAT_BRUSHED,
        ),
        (
            chamfer_box((0.26, 1.30, 0.060), 0.006),
            transform((0.10, 0.0, 0.655)),
            MAT_DARK_METAL,
        ),
    ]
    for leg_x in (-0.36, 0.36):
        for leg_y in (-0.95, 0.95):
            parts.extend(extrusion_parts(0.06, 0.66, transform((leg_x, leg_y, 0.36))))
            parts.extend(levelling_foot_parts(transform((leg_x, leg_y, 0.0))))
        parts.extend(
            extrusion_parts(
                0.05,
                1.94,
                transform((leg_x, 0.0, 0.695), rpy=(math.pi / 2.0, 0.0, 0.0)),
            )
        )

    # Monitor stand: one post on the back edge carrying a crossbar.
    parts.append(
        (
            chamfer_box((0.17, 0.28, 0.040), 0.006),
            transform((-0.34, 0.0, desk_top + 0.020)),
            MAT_CABINET_TRIM,
        )
    )
    parts.append(
        (
            chamfer_cylinder(0.034, 0.30, sections=24),
            transform((-0.34, 0.0, desk_top + 0.170)),
            MAT_BRUSHED,
        )
    )
    parts.append(
        (
            chamfer_box((0.055, 1.56, 0.055), 0.008),
            transform((-0.34, 0.0, desk_top + 0.300)),
            MAT_CABINET_TRIM,
        )
    )

    # Screen centres a little over a third of a metre above the desk, which
    # is where they sit for someone seated at it.
    screen_height = desk_top + 0.37
    screens = []
    # The outer panels turn towards the seat, not away from it: a monitor at
    # +Y has to swing its face towards -Y to point at the person.
    for offset_y, tilt, kind in (
        (0.71, math.radians(-24.0), "run"),
        (0.0, 0.0, "policy"),
        (-0.71, math.radians(24.0), "cell"),
    ):
        # Each panel is turned in towards the seat, so the three of them wrap
        # the person rather than lying flat across the desk.
        mount = transform((-0.30, offset_y, screen_height)) @ rotate_z(tilt)
        parts.append(
            (
                chamfer_box((0.06, 0.10, 0.06), 0.008),
                transform((-0.335, offset_y, screen_height)),
                MAT_CABINET_TRIM,
            )
        )
        parts.append((chamfer_box((0.028, 0.700, 0.420), 0.006), mount, MAT_CABINET_TRIM))
        parts.append(
            (
                chamfer_box((0.020, 0.16, 0.030), 0.004),
                mount @ transform((0.0, 0.0, -0.208)),
                MAT_CABINET_TRIM,
            )
        )
        screens.append((mount, kind))
    scene.add(assembly_mesh(parts), pose=root)
    for mount, kind in screens:
        scene.add(
            panel_mesh(
                0.670,
                0.390,
                make_training_screen_texture(kind),
                mat=screen_material(make_training_screen_texture(kind)),
            ),
            pose=root @ mount @ transform((0.016, 0.0, 0.0)) @ rotate_z(-math.pi / 2.0),
        )

    # Desk furniture: keyboard and mouse, nothing else on the top.
    desk_parts = [
        (
            chamfer_box((0.155, 0.44, 0.016), 0.004),
            transform((0.10, 0.02, desk_top + 0.008)),
            MAT_DARK_METAL,
        ),
        (
            chamfer_box((0.125, 0.40, 0.006), 0.002),
            transform((0.10, 0.02, desk_top + 0.017)),
            MAT_BLACK,
        ),
        (
            fillet_box((0.065, 0.105, 0.032), 0.012),
            transform((0.13, -0.36, desk_top + 0.016)),
            MAT_DARK_METAL,
        ),
        # The workstation itself lives under the desk.
        (
            chamfer_box((0.230, 0.500, 0.500), 0.010),
            transform((-0.16, 0.62, 0.28)),
            MAT_CABINET_TRIM,
        ),
        (
            chamfer_box((0.020, 0.460, 0.460), 0.006),
            transform((-0.038, 0.62, 0.28)),
            MAT_DARK_METAL,
        ),
        (
            chamfer_box((0.014, 0.070, 0.014), 0.003),
            transform((-0.030, 0.44, 0.47)),
            MAT_LAMP_GREEN,
        ),
        (
            chamfer_box((0.010, 0.030, 0.010), 0.002),
            transform((-0.030, 0.44, 0.44)),
            MAT_AMBER,
        ),
    ]
    for vent_z in np.linspace(0.10, 0.34, 8):
        desk_parts.append(
            (
                chamfer_box((0.012, 0.34, 0.012), 0.002),
                transform((-0.036, 0.66, vent_z)),
                MAT_BLACK,
            )
        )
    scene.add(assembly_mesh(desk_parts), pose=root)

    # Task chair: seat towards the desk, back to the bay, and swung a little
    # off square the way a chair someone has just got up from always is.
    chair = transform((0.92, 0.10, 0.0)) @ rotate_z(math.pi + math.radians(24.0))
    chair_parts = []
    for index in range(5):
        spoke = 2.0 * math.pi * index / 5.0 + math.radians(18.0)
        chair_parts.append(
            (
                tapered_box(0.075, 0.045, 0.30, 0.045),
                chair
                @ transform(
                    (
                        0.15 * math.cos(spoke),
                        0.15 * math.sin(spoke),
                        0.055,
                    ),
                    rpy=(0.0, math.pi / 2.0, spoke),
                ),
                MAT_BRUSHED,
            )
        )
        chair_parts.append(
            (
                chamfer_cylinder(0.030, 0.026, sections=18),
                chair
                @ transform(
                    (
                        0.30 * math.cos(spoke),
                        0.30 * math.sin(spoke),
                        0.030,
                    ),
                    rpy=(math.pi / 2.0, 0.0, 0.0),
                ),
                MAT_BLACK,
            )
        )
    chair_parts.extend(
        (
            (
                chamfer_cylinder(0.055, 0.05, sections=24),
                chair @ transform((0.0, 0.0, 0.085)),
                MAT_DARK_METAL,
            ),
            (
                chamfer_cylinder(0.036, 0.30, sections=20),
                chair @ transform((0.0, 0.0, 0.255)),
                MAT_BRUSHED,
            ),
            (
                chamfer_cylinder(0.055, 0.07, sections=20),
                chair @ transform((0.0, 0.0, 0.375)),
                MAT_DARK_METAL,
            ),
            (
                fillet_box((0.47, 0.46, 0.095), 0.030),
                chair @ transform((0.0, 0.0, 0.455)),
                MAT_BLACK,
            ),
            (
                chamfer_box((0.10, 0.30, 0.055), 0.010),
                chair @ transform((-0.20, 0.0, 0.50), rpy=(0.0, -0.5, 0.0)),
                MAT_DARK_METAL,
            ),
            (
                fillet_box((0.070, 0.45, 0.52), 0.030),
                chair @ transform((-0.245, 0.0, 0.79), rpy=(0.0, math.radians(-14.0), 0.0)),
                MAT_BLACK,
            ),
        )
    )
    for arm_y in (-0.245, 0.245):
        chair_parts.append(
            (
                chamfer_box((0.045, 0.045, 0.20), 0.008),
                chair @ transform((-0.10, arm_y, 0.585)),
                MAT_DARK_METAL,
            )
        )
        chair_parts.append(
            (
                fillet_box((0.24, 0.070, 0.030), 0.012),
                chair @ transform((-0.03, arm_y, 0.695)),
                MAT_BLACK,
            )
        )
    scene.add(assembly_mesh(chair_parts), pose=root)


def add_dynamic(scene, dynamic_nodes, mesh, base_pose, kind):
    dynamic_nodes.append(
        DynamicNode(
            node=scene.add(mesh, pose=base_pose),
            base_pose=base_pose,
            kind=kind,
        )
    )


def add_station_hardware(scene, dynamic_nodes, cell_index, cx, cy):
    """Stopper, lift-and-clamp, sensors, status light and station services."""
    side = -1.0 if cx < 0 else 1.0

    # Lift-and-clamp unit under the belt, with the pallet locating pins.
    clamp_body = [
        (chamfer_box((0.38, 0.34, 0.20), 0.008), transform((0.0, cy, 0.175)), MAT_DARK_METAL),
        (
            chamfer_box((0.30, 0.10, 0.075), 0.006),
            transform((0.0, cy - 0.20, 0.24)),
            MAT_CABINET_TRIM,
        ),
    ]
    for guide_x in (-0.15, 0.15):
        clamp_body.append(
            (
                chamfer_cylinder(0.020, 0.15, sections=22),
                transform((guide_x, cy, 0.315)),
                MAT_BRUSHED,
            )
        )
        clamp_body.append(
            (
                chamfer_cylinder(0.030, 0.030, sections=22),
                transform((guide_x, cy, 0.262)),
                MAT_STEEL,
            )
        )
    for fitting_x in (-0.05, 0.05):
        clamp_body.append(
            (
                chamfer_cylinder(0.010, 0.030, sections=12),
                transform((fitting_x, cy - 0.255, 0.24), rpy=(math.pi / 2.0, 0.0, 0.0)),
                MAT_HOSE,
            )
        )
    clamp_body.extend(
        bolt_row_parts(
            [(x, cy + y, 0.276) for x in (-0.16, 0.16) for y in (-0.13, 0.13)],
            0.014,
            0.008,
        )
    )
    scene.add(assembly_mesh(clamp_body))
    clamp_platen = [
        (chamfer_box((0.34, 0.30, 0.030), 0.005), None, MAT_BRUSHED),
    ]
    for pin_x in (-0.12, 0.12):
        clamp_platen.append(
            (
                trimesh.creation.cylinder(radius=0.012, height=0.055, sections=20),
                transform((pin_x, 0.0, 0.034)),
                MAT_STEEL,
            )
        )
        clamp_platen.append(
            (
                trimesh.creation.cone(radius=0.012, height=0.016, sections=20),
                transform((pin_x, 0.0, 0.061)),
                MAT_STEEL,
            )
        )
        clamp_platen.append(
            (
                chamfer_cylinder(0.026, 0.012, sections=20),
                transform((pin_x, 0.0, 0.020)),
                MAT_DARK_METAL,
            )
        )
    for pad_y in (-0.115, 0.115):
        clamp_platen.append(
            (
                chamfer_box((0.26, 0.030, 0.012), 0.003),
                transform((0.0, pad_y, 0.020)),
                MAT_DARK_METAL,
            )
        )
    add_dynamic(
        scene,
        dynamic_nodes,
        assembly_mesh(clamp_platen),
        transform((0.0, cy, 0.378)),
        "clamp",
    )

    # Pneumatic stopper at the downstream edge of the station, bracketed to
    # the outside of the frame where it can actually be serviced.
    stop_y = cy + 0.46
    stopper_parts = [
        (chamfer_box((0.20, 0.15, 0.028), 0.005), transform((0.52, stop_y, 0.235)), MAT_BRUSHED),
        (chamfer_box((0.12, 0.13, 0.20), 0.006), transform((0.57, stop_y, 0.345)), MAT_STEEL),
        (
            chamfer_cylinder(0.028, 0.16, sections=22),
            transform((0.57, stop_y, 0.505)),
            MAT_BRUSHED,
        ),
        (
            chamfer_cylinder(0.034, 0.020, sections=22),
            transform((0.57, stop_y, 0.435)),
            MAT_STEEL,
        ),
        (chamfer_box((0.30, 0.045, 0.030), 0.005), transform((0.42, stop_y, 0.425)), MAT_STEEL),
        # Shock absorber alongside the cylinder.
        (
            chamfer_cylinder(0.014, 0.10, sections=16),
            transform((0.505, stop_y, 0.50)),
            MAT_DARK_METAL,
        ),
    ]
    for tie_x in (0.548, 0.592):
        stopper_parts.append(
            (
                trimesh.creation.cylinder(radius=0.005, height=0.15, sections=10),
                transform((tie_x, stop_y, 0.505)),
                MAT_STEEL,
            )
        )
    for fitting_z in (0.30, 0.40):
        stopper_parts.append(
            (
                chamfer_cylinder(0.011, 0.05, sections=12),
                transform((0.635, stop_y, fitting_z), rpy=(0.0, math.pi / 2, 0.0)),
                MAT_HOSE,
            )
        )
        stopper_parts.append(
            (
                trimesh.creation.cylinder(radius=0.016, height=0.014, sections=6),
                transform((0.615, stop_y, fitting_z), rpy=(0.0, math.pi / 2, 0.0)),
                MAT_BRUSHED,
            )
        )
    scene.add(assembly_mesh(stopper_parts))
    add_dynamic(
        scene,
        dynamic_nodes,
        assembly_mesh(
            [
                (chamfer_box((0.075, 0.034, 0.145), 0.006), None, MAT_DARK_METAL),
                (
                    chamfer_cylinder(0.018, 0.030, sections=18),
                    transform((0.0, 0.0, 0.058), rpy=(math.pi / 2.0, 0.0, 0.0)),
                    MAT_STEEL,
                ),
            ]
        ),
        transform((0.285, stop_y, 0.375)),
        "stopper",
    )

    # Pallet-present photoelectric sensor and the fixture RFID head.
    scene.add(
        assembly_mesh(
            [
                (
                    chamfer_box((0.040, 0.055, 0.095), 0.005),
                    transform((0.492, cy + 0.30, 0.44)),
                    MAT_DARK_METAL,
                ),
                (
                    chamfer_box((0.012, 0.030, 0.030), 0.003),
                    transform((0.469, cy + 0.30, 0.455)),
                    MAT_AMBER,
                ),
                (
                    chamfer_box((0.010, 0.014, 0.010), 0.002),
                    transform((0.470, cy + 0.30, 0.410)),
                    MAT_LAMP_AMBER,
                ),
                (
                    chamfer_box((0.030, 0.070, 0.012), 0.003),
                    transform((0.505, cy + 0.30, 0.393)),
                    MAT_BRUSHED,
                ),
                (
                    chamfer_cylinder(0.006, 0.045, sections=10),
                    transform((0.492, cy + 0.30, 0.512)),
                    MAT_HOSE,
                ),
                (
                    chamfer_cylinder(0.032, 0.055, sections=26),
                    transform((0.485, cy - 0.16, 0.42), rpy=(0.0, math.pi / 2.0, 0.0)),
                    MAT_CABINET_TRIM,
                ),
                (
                    chamfer_box((0.020, 0.075, 0.075), 0.004),
                    transform((0.505, cy - 0.16, 0.42)),
                    MAT_CABINET_TRIM,
                ),
            ]
        )
    )

    # Three-tier status light carried on the stocker frame.
    tower_x = side * STOCKER_OUTER_X
    tower_y = cy + 0.43
    tower_parts = []
    if fetches_component(cell_index):
        tower_parts.append(
            (
                chamfer_cylinder(0.019, 0.62, sections=20),
                transform((tower_x, tower_y, 1.55)),
                MAT_BRUSHED,
            )
        )
        # Clamp where the pole is bracketed to the rack.
        tower_parts.append(
            (
                chamfer_box((0.055, 0.055, 0.050), 0.005),
                transform((tower_x, tower_y, 1.265)),
                MAT_CABINET_TRIM,
            )
        )
    else:
        # No stocker frame to carry it, so the light gets its own stand.
        tower_parts.append(
            (
                chamfer_cylinder(0.028, 1.85, sections=20),
                transform((tower_x, tower_y, 0.935)),
                MAT_BRUSHED,
            )
        )
        tower_parts.append(
            (
                chamfer_box((0.22, 0.22, 0.030), 0.006),
                transform((tower_x, tower_y, 0.02)),
                MAT_STEEL,
            )
        )
        tower_parts.append(
            (
                chamfer_cylinder(0.055, 0.045, sections=24),
                transform((tower_x, tower_y, 0.055)),
                MAT_CABINET_TRIM,
            )
        )
        tower_parts.extend(
            bolt_row_parts(
                [(tower_x + x, tower_y + y, 0.035) for x in (-0.085, 0.085) for y in (-0.085, 0.085)],
                0.016,
                0.010,
            )
        )
    lamp_z = (1.885, 1.940, 1.995)
    for height in lamp_z:
        tower_parts.append(
            (
                chamfer_cylinder(0.045, 0.052, chamfer=0.004, sections=28),
                transform((tower_x, tower_y, height)),
                MAT_LAMP_OFF,
            )
        )
        # Dark spacer between segments: what makes a stack read as a stack.
        tower_parts.append(
            (
                chamfer_cylinder(0.047, 0.007, sections=28),
                transform((tower_x, tower_y, height - 0.028)),
                MAT_CABINET_TRIM,
            )
        )
    tower_parts.append(
        (
            chamfer_cylinder(0.050, 0.022, chamfer=0.008, sections=28),
            transform((tower_x, tower_y, 2.032)),
            MAT_CABINET_TRIM,
        )
    )
    tower_parts.append(
        (
            trimesh.creation.icosphere(subdivisions=1, radius=0.048),
            transform((tower_x, tower_y, 2.043)),
            MAT_CABINET_TRIM,
        )
    )
    scene.add(assembly_mesh(tower_parts))
    add_dynamic(
        scene,
        dynamic_nodes,
        turned_mesh(0.047, 0.050, MAT_LAMP_GREEN, chamfer=0.004, sections=28),
        transform((tower_x, tower_y, lamp_z[0])),
        "lamp_work",
    )
    add_dynamic(
        scene,
        dynamic_nodes,
        turned_mesh(0.047, 0.050, MAT_LAMP_AMBER, chamfer=0.004, sections=28),
        transform((tower_x, tower_y, lamp_z[1])),
        "lamp_index",
    )

    # Station placard hung over the walkway, facing down the line.
    scene.add(
        panel_mesh(
            0.62,
            0.21,
            make_sign_texture(STATION_LABELS[cell_index], STATION_NAMES[cell_index]),
        ),
        pose=transform((side * SIGN_X, cy, 2.34)),
    )
    sign_parts = [
        (
            chamfer_box((0.64, 0.035, 0.23), 0.006),
            transform((side * SIGN_X, cy - 0.024, 2.34)),
            MAT_CABINET_TRIM,
        )
    ]
    for rod_x in (-0.24, 0.24):
        sign_parts.append(
            (
                chamfer_cylinder(0.010, SIGN_RAIL_Z - 2.45, sections=12),
                transform((side * SIGN_X + rod_x, cy, (SIGN_RAIL_Z + 2.45) / 2.0)),
                MAT_BRUSHED,
            )
        )
        # Rail clamp at the top, bracket at the sign end.
        sign_parts.append(
            (
                chamfer_box((0.040, 0.090, 0.045), 0.005),
                transform((side * SIGN_X + rod_x, cy, SIGN_RAIL_Z - 0.055)),
                MAT_CABINET_TRIM,
            )
        )
        sign_parts.append(
            (
                chamfer_box((0.036, 0.050, 0.030), 0.004),
                transform((side * SIGN_X + rod_x, cy - 0.010, 2.462)),
                MAT_CABINET_TRIM,
            )
        )
    scene.add(assembly_mesh(sign_parts))

    # Robot controller beside the cell plus its umbilical to the base.
    box_x = cx + side * 0.72
    controller_parts = [
        (
            chamfer_box((0.42, 0.52, 0.60), 0.010),
            transform((box_x, cy - 0.52, 0.27)),
            MAT_CABINET,
        ),
        (
            chamfer_box((0.43, 0.10, 0.045), 0.006),
            transform((box_x, cy - 0.52, 0.585)),
            MAT_CABINET_TRIM,
        ),
        (
            chamfer_box((0.012, 0.16, 0.22), 0.004),
            transform((box_x - side * 0.215, cy - 0.52, 0.34)),
            MAT_CABINET_TRIM,
        ),
        # Door seam, handle and the vent that every controller carries.
        (
            chamfer_box((0.008, 0.44, 0.50), 0.002),
            transform((box_x + side * 0.212, cy - 0.52, 0.28)),
            MAT_CABINET_TRIM,
        ),
        (
            chamfer_box((0.030, 0.028, 0.16), 0.005),
            transform((box_x + side * 0.230, cy - 0.66, 0.30)),
            MAT_BRUSHED,
        ),
        (
            trimesh.creation.cylinder(radius=0.026, height=0.014, sections=24),
            transform(
                (box_x + side * 0.216, cy - 0.36, 0.44),
                rpy=(0.0, math.pi / 2.0, 0.0),
            ),
            MAT_DARK_METAL,
        ),
        (
            chamfer_box((0.42, 0.44, 0.030), 0.005),
            transform((box_x, cy - 0.52, -0.010)),
            MAT_CABINET_TRIM,
        ),
        (
            trimesh.creation.cylinder(radius=0.028, height=0.60, sections=16),
            transform(
                (box_x - side * 0.30, cy - 0.36, 0.12),
                rpy=(0.0, math.pi / 2 - side * 0.5, 0.55 * side),
            ),
            MAT_HOSE,
        ),
    ]
    for vent_z in np.linspace(0.10, 0.22, 5):
        controller_parts.append(
            (
                chamfer_box((0.010, 0.30, 0.012), 0.002),
                transform((box_x + side * 0.214, cy - 0.52, vent_z)),
                MAT_DARK_METAL,
            )
        )
    scene.add(assembly_mesh(controller_parts))

    rack_center_x = side * (STOCKER_INNER_X + STOCKER_OUTER_X) / 2.0
    if fetches_component(cell_index):
        # The parts themselves are presented by the stocker; what belongs to
        # the station here is the feed controller under the rack.
        scene.add(
            assembly_mesh(
                [
                    (
                        chamfer_box((0.28, 0.36, 0.20), 0.008),
                        transform((rack_center_x, cy, 0.22)),
                        MAT_CABINET_TRIM,
                    ),
                    (
                        chamfer_box((0.012, 0.24, 0.10), 0.003),
                        transform((rack_center_x - side * 0.146, cy, 0.26)),
                        MAT_DARK_METAL,
                    ),
                ]
            )
        )
    else:
        # Measurement cabinet in place of the stocker.
        cabinet_parts = [
            (
                chamfer_box((0.46, 0.60, 1.02), 0.010),
                transform((rack_center_x, cy, 0.52)),
                MAT_CABINET,
            ),
            (
                chamfer_box((0.48, 0.62, 0.06), 0.008),
                transform((rack_center_x, cy, 1.05)),
                MAT_CABINET_TRIM,
            ),
            (
                chamfer_box((0.44, 0.56, 0.045), 0.008),
                transform((rack_center_x, cy, 0.020)),
                MAT_CABINET_TRIM,
            ),
            (
                chamfer_box((0.030, 0.36, 0.26), 0.005),
                transform((rack_center_x - side * 0.228, cy + 0.06, 0.86)),
                MAT_CABINET_TRIM,
            ),
            (
                chamfer_box((0.020, 0.32, 0.22), 0.004),
                transform((rack_center_x - side * 0.242, cy + 0.06, 0.86)),
                MAT_SCREEN,
            ),
            (
                chamfer_box((0.026, 0.030, 0.20), 0.005),
                transform((rack_center_x - side * 0.246, cy - 0.22, 0.52)),
                MAT_BRUSHED,
            ),
            (
                trimesh.creation.cylinder(radius=0.014, height=1.15, sections=12),
                transform(
                    (rack_center_x - side * 0.28, cy - 0.22, 0.62),
                    rpy=(0.0, 0.45 * side, 0.0),
                ),
                MAT_HOSE,
            ),
        ]
        for vent_z in np.linspace(0.20, 0.38, 6):
            cabinet_parts.append(
                (
                    chamfer_box((0.012, 0.34, 0.014), 0.003),
                    transform((rack_center_x - side * 0.232, cy, vent_z)),
                    MAT_DARK_METAL,
                )
            )
        scene.add(assembly_mesh(cabinet_parts))


def add_line_services(scene):
    """Cable ducts, air header, safety devices and line signage."""
    line_y_min = CELL_Y_START - 3.4
    line_y_max = CELL_LAYOUT[-1][1] + 1.9
    span = line_y_max - line_y_min
    center = (line_y_min + line_y_max) / 2.0

    # The placard rail runs past both ends of the line so the orbit never
    # catches it stopping in mid-air.
    rail_min = line_y_min - 2.1
    rail_max = LIGHT_Y_MAX
    for side in (-1.0, 1.0):
        service_parts = [
            (
                chamfer_box((0.07, rail_max - rail_min, 0.07), 0.006),
                transform((side * SIGN_X, (rail_max + rail_min) / 2.0, SIGN_RAIL_Z)),
                MAT_TRUSS,
            ),
            # Cable duct clipped to the conveyor stands, with its lid.
            (
                chamfer_box((0.13, span, 0.11), 0.006),
                transform((side * 0.63, center, 0.155)),
                MAT_DUCT,
            ),
            (
                chamfer_box((0.14, span, 0.018), 0.004),
                transform((side * 0.63, center, 0.216)),
                MAT_CABINET_TRIM,
            ),
            # Compressed-air header with a drop leg at every station.
            (
                chamfer_cylinder(0.032, span, sections=22),
                transform((side * 1.42, center, 2.62), rpy=(math.pi / 2, 0.0, 0.0)),
                MAT_BRUSHED,
            ),
        ]
        for post_y in (rail_min + 0.2, line_y_max + 0.9, rail_max - 0.2):
            service_parts.append(
                (
                    chamfer_cylinder(0.035, SIGN_RAIL_Z, sections=18),
                    transform((side * SIGN_X, post_y, SIGN_RAIL_Z / 2.0)),
                    MAT_TRUSS,
                )
            )
            service_parts.append(
                (
                    chamfer_box((0.20, 0.20, 0.020), 0.005),
                    transform((side * SIGN_X, post_y, 0.010)),
                    MAT_STEEL,
                )
            )
            service_parts.extend(
                bolt_row_parts(
                    [(side * SIGN_X + x, post_y + y, 0.020) for x in (-0.070, 0.070) for y in (-0.070, 0.070)],
                    0.018,
                    0.011,
                )
            )
            # Gusset where the post meets the rail.
            service_parts.append(
                (
                    chamfer_box((0.012, 0.14, 0.14), 0.004),
                    transform((side * SIGN_X, post_y, SIGN_RAIL_Z - 0.10)),
                    MAT_TRUSS,
                )
            )
        for clip_y in np.arange(center - span / 2.0 + 0.4, center + span / 2.0, 0.9):
            service_parts.append(
                (
                    chamfer_box((0.155, 0.020, 0.030), 0.004),
                    transform((side * 0.63, clip_y, 0.212)),
                    MAT_BRUSHED,
                )
            )
        for hanger_y in np.linspace(line_y_min + 1.0, line_y_max - 1.0, 7):
            service_parts.append(
                (
                    chamfer_cylinder(0.012, 0.70, sections=12),
                    transform((side * 1.42, hanger_y, 2.97)),
                    MAT_BRUSHED,
                )
            )
            # Pipe clamp at every hanger.
            service_parts.append(
                (
                    chamfer_box((0.080, 0.024, 0.090), 0.005),
                    transform((side * 1.42, hanger_y, 2.645)),
                    MAT_BRUSHED,
                )
            )
        scene.add(assembly_mesh(service_parts))
    for cell_index, (cx, cy, _) in enumerate(CELL_LAYOUT):
        side = -1.0 if cx < 0 else 1.0
        # Drop leg: tee off the header, then a filter-regulator on the wall
        # of the cell, which is what a station's air actually goes through.
        drop_parts = [
            (
                trimesh.creation.cylinder(radius=0.014, height=1.70, sections=12),
                transform((side * 1.42, cy + 0.16, 1.76)),
                MAT_HOSE,
            ),
            (
                chamfer_cylinder(0.026, 0.055, sections=18),
                transform((side * 1.42, cy + 0.16, 2.585)),
                MAT_BRUSHED,
            ),
            (
                chamfer_box((0.10, 0.14, 0.20), 0.007),
                transform((side * 1.42, cy + 0.16, 0.98)),
                MAT_BRUSHED,
            ),
            (
                chamfer_cylinder(0.040, 0.075, sections=22),
                transform((side * 1.42, cy + 0.115, 0.845)),
                MAT_DARK_METAL,
            ),
            (
                chamfer_cylinder(0.040, 0.075, sections=22),
                transform((side * 1.42, cy + 0.205, 0.845)),
                MAT_DARK_METAL,
            ),
            (
                chamfer_cylinder(0.026, 0.020, sections=20),
                transform(
                    (side * 1.47, cy + 0.16, 1.045),
                    rpy=(0.0, side * math.pi / 2.0, 0.0),
                ),
                MAT_WHITE,
            ),
        ]
        scene.add(assembly_mesh(drop_parts))

    # A single line control panel, its doors facing the walkway.
    add_control_cabinet(scene, -CABINET_X, CABINET_Y, 1.0)

    # The training run is watched from a desk on the far side of the line
    # from the control panel, turned so the screens face down the bay.
    add_monitoring_station(scene, STATION_CENTRE, STATION_YAW)

    # Barrier between the stockers and the operator panels, keeping the
    # walkway out of the cells' working space. Posts and rails rather than
    # mesh: a woven panel at this distance is a screenful of half-pixel wires
    # that crawl from frame to frame.
    for side in (-1.0, 1.0):
        barrier = []
        jambs = (
            BARRIER_GATE_Y - BARRIER_GATE_WIDTH / 2.0,
            BARRIER_GATE_Y + BARRIER_GATE_WIDTH / 2.0,
        )
        posts = [
            post_y
            for post_y in np.arange(BARRIER_Y_MIN, BARRIER_Y_MAX + 0.01, 2.0)
            if abs(post_y - BARRIER_GATE_Y) > BARRIER_GATE_WIDTH / 2.0 + 0.35
        ]
        for post_y in list(posts) + list(jambs):
            barrier.extend(
                extrusion_parts(
                    0.06,
                    BARRIER_HEIGHT,
                    transform((side * BARRIER_X, post_y, BARRIER_HEIGHT / 2.0 + 0.02)),
                    mat=MAT_SAFETY_YELLOW,
                    core_mat=MAT_CABINET_TRIM,
                )
            )
            barrier.append(
                (
                    chamfer_box((0.16, 0.16, 0.020), 0.004),
                    transform((side * BARRIER_X, post_y, 0.010)),
                    MAT_STEEL,
                )
            )
            barrier.extend(
                bolt_row_parts(
                    [(side * BARRIER_X + x, post_y + y, 0.020) for x in (-0.055, 0.055) for y in (-0.055, 0.055)],
                    0.014,
                    0.009,
                )
            )
        for run_min, run_max in (
            (BARRIER_Y_MIN, jambs[0]),
            (jambs[1], BARRIER_Y_MAX),
        ):
            for rail_z in (0.52, 1.02):
                barrier.append(
                    (
                        chamfer_cylinder(0.021, run_max - run_min, sections=16),
                        transform(
                            (side * BARRIER_X, (run_min + run_max) / 2.0, rail_z),
                            rpy=(math.pi / 2.0, 0.0, 0.0),
                        ),
                        MAT_SAFETY_YELLOW,
                    )
                )
            # Toe board along the bottom of each run.
            barrier.append(
                (
                    chamfer_box((0.014, run_max - run_min, 0.10), 0.003),
                    transform((side * BARRIER_X, (run_min + run_max) / 2.0, 0.09)),
                    MAT_SAFETY_YELLOW,
                )
            )
        # The opening is a gate, not a hole: a leaf across it on hinges, with
        # a latch and the interlock switch that makes it worth having.
        leaf = BARRIER_GATE_WIDTH - 0.10
        for rail_z in (0.52, 1.02):
            barrier.append(
                (
                    chamfer_cylinder(0.020, leaf, sections=16),
                    transform(
                        (side * BARRIER_X, BARRIER_GATE_Y, rail_z),
                        rpy=(math.pi / 2.0, 0.0, 0.0),
                    ),
                    MAT_SAFETY_YELLOW,
                )
            )
        for stile_y in (
            BARRIER_GATE_Y - leaf / 2.0,
            BARRIER_GATE_Y + leaf / 2.0,
        ):
            barrier.append(
                (
                    chamfer_box((0.040, 0.040, BARRIER_HEIGHT - 0.10), 0.005),
                    transform((side * BARRIER_X, stile_y, (BARRIER_HEIGHT - 0.10) / 2.0 + 0.06)),
                    MAT_SAFETY_YELLOW,
                )
            )
        barrier.append(
            (
                chamfer_box((0.014, leaf, 0.10), 0.003),
                transform((side * BARRIER_X, BARRIER_GATE_Y, 0.09)),
                MAT_SAFETY_YELLOW,
            )
        )
        for hinge_z in (0.42, 1.00):
            barrier.append(
                (
                    chamfer_cylinder(0.022, 0.075, sections=16),
                    transform((side * BARRIER_X, jambs[0] + 0.035, hinge_z)),
                    MAT_CABINET_TRIM,
                )
            )
        # Latch on the closing stile, and the interlock on the jamb.
        barrier.append(
            (
                chamfer_box((0.050, 0.090, 0.055), 0.006),
                transform((side * BARRIER_X, BARRIER_GATE_Y + leaf / 2.0 - 0.02, 0.86)),
                MAT_CABINET_TRIM,
            )
        )
        barrier.append(
            (
                chamfer_cylinder(0.016, 0.11, sections=14),
                transform(
                    (
                        side * (BARRIER_X + 0.055),
                        BARRIER_GATE_Y + leaf / 2.0 - 0.02,
                        0.86,
                    ),
                    rpy=(0.0, math.pi / 2.0, 0.0),
                ),
                MAT_BRUSHED,
            )
        )
        barrier.append(
            (
                chamfer_box((0.045, 0.055, 0.11), 0.005),
                transform((side * BARRIER_X, jambs[1] - 0.03, 0.86)),
                MAT_CABINET_TRIM,
            )
        )
        barrier.append(
            (
                chamfer_box((0.012, 0.020, 0.020), 0.003),
                transform((side * (BARRIER_X - 0.030), jambs[1] - 0.03, 0.91)),
                MAT_LAMP_GREEN,
            )
        )
        scene.add(assembly_mesh(barrier))

    # Operator panels along both walkways, each carrying its emergency stop.
    for side in (-1.0, 1.0):
        for post_y in np.linspace(CELL_Y_START - 0.6, CELL_Y_START + 9.4, 4):
            add_operator_panel(scene, side * (WALK_INNER_X - 0.30), post_y, side)

    # Safety laser scanners covering the approach to the cobot cells.
    for side in (-1.0, 1.0):
        for scanner_y in (CELL_Y_START - 1.5, CELL_LAYOUT[-1][1] + 1.5):
            scanner_x = side * (WALK_INNER_X - 0.10)
            scene.add(
                assembly_mesh(
                    [
                        (
                            chamfer_box((0.16, 0.16, 0.30), 0.008),
                            transform((scanner_x, scanner_y, 0.15)),
                            MAT_STEEL,
                        ),
                        (
                            chamfer_box((0.20, 0.20, 0.020), 0.005),
                            transform((scanner_x, scanner_y, 0.010)),
                            MAT_STEEL,
                        ),
                        (
                            chamfer_cylinder(0.075, 0.11, sections=32),
                            transform((scanner_x, scanner_y, 0.355)),
                            MAT_SCANNER,
                        ),
                        (
                            chamfer_cylinder(0.078, 0.022, sections=32),
                            transform((scanner_x, scanner_y, 0.322)),
                            MAT_CYAN,
                        ),
                        (
                            chamfer_cylinder(0.072, 0.014, sections=32),
                            transform((scanner_x, scanner_y, 0.418)),
                            MAT_CABINET_TRIM,
                        ),
                        (
                            chamfer_box((0.10, 0.030, 0.035), 0.004),
                            transform((scanner_x, scanner_y - 0.085, 0.395)),
                            MAT_CABINET_TRIM,
                        ),
                        (
                            chamfer_box((0.13, 0.013, 0.055), 0.003),
                            transform((scanner_x, scanner_y - 0.086, 0.24)),
                            MAT_SAFETY_YELLOW,
                        ),
                    ]
                )
            )

    # Light curtains guarding the pallet infeed.
    for guard_x in (-0.72, 0.72):
        inboard = -math.copysign(1.0, guard_x)
        curtain_parts = [
            (
                chamfer_box((0.075, 0.075, 1.30), 0.008),
                transform((guard_x, CELL_Y_START - 3.05, 0.63)),
                MAT_SAFETY_YELLOW,
            ),
            (
                chamfer_box((0.030, 0.028, 1.02), 0.004),
                transform((guard_x + inboard * 0.045, CELL_Y_START - 3.05, 0.70)),
                MAT_CABINET_TRIM,
            ),
            (
                chamfer_box((0.014, 0.020, 0.96), 0.003),
                transform((guard_x + inboard * 0.058, CELL_Y_START - 3.05, 0.70)),
                MAT_DARK_METAL,
            ),
            (
                chamfer_box((0.16, 0.16, 0.018), 0.004),
                transform((guard_x, CELL_Y_START - 3.05, 0.008)),
                MAT_STEEL,
            ),
            (
                chamfer_cylinder(0.012, 0.045, sections=12),
                transform((guard_x, CELL_Y_START - 3.05, 1.30)),
                MAT_HOSE,
            ),
        ]
        for cap_z in (0.20, 1.20):
            curtain_parts.append(
                (
                    chamfer_box((0.050, 0.045, 0.045), 0.005),
                    transform((guard_x + inboard * 0.045, CELL_Y_START - 3.05, cap_z)),
                    MAT_CABINET_TRIM,
                )
            )
        scene.add(assembly_mesh(curtain_parts))

    # Production board over the head of the line. Its case sits behind the
    # face, or it would hide the very thing it carries.
    board_y = CELL_Y_START - 3.9
    board_z = 2.62
    scene.add(
        panel_mesh(2.70, 1.26, make_andon_texture()),
        pose=transform((0.0, board_y, board_z)),
    )
    board_parts = [
        (
            chamfer_box((2.84, 0.09, 1.40), 0.012),
            transform((0.0, board_y - 0.055, board_z)),
            MAT_CABINET_TRIM,
        ),
    ]
    # Bezel around the face, so the board has a case rather than a backing.
    for bezel_x in (-1.375, 1.375):
        board_parts.append(
            (
                chamfer_box((0.055, 0.055, 1.36), 0.008),
                transform((bezel_x, board_y - 0.012, board_z)),
                MAT_CABINET_TRIM,
            )
        )
    for bezel_z in (board_z - 0.655, board_z + 0.655):
        board_parts.append(
            (
                chamfer_box((2.80, 0.055, 0.055), 0.008),
                transform((0.0, board_y - 0.012, bezel_z)),
                MAT_CABINET_TRIM,
            )
        )
    for rod_x in (-1.02, 1.02):
        board_parts.append(
            (
                chamfer_cylinder(0.016, TRUSS_LOWER - 0.08 - 3.32, sections=14),
                transform((rod_x, board_y - 0.055, (TRUSS_LOWER - 0.08 + 3.32) / 2.0)),
                MAT_BRUSHED,
            )
        )
        board_parts.append(
            (
                chamfer_box((0.10, 0.10, 0.045), 0.006),
                transform((rod_x, board_y - 0.055, 3.335)),
                MAT_CABINET_TRIM,
            )
        )
    scene.add(assembly_mesh(board_parts))


def add_infeed_outfeed(scene):
    """Empty-pallet infeed and the finished-product takeoff."""
    # The empty-pallet magazine stands beside the line, not on it: at the
    # centreline its stack would sit inside the passing pallets.
    infeed_y = CELL_Y_START - 4.6
    infeed_x = 1.62
    infeed_parts = [
        (
            chamfer_box((1.10, 1.30, 0.09), 0.008),
            transform((infeed_x, infeed_y, 0.355)),
            MAT_BRUSHED,
        ),
    ]
    for leg_x in (infeed_x - 0.44, infeed_x + 0.44):
        for leg_y in (infeed_y - 0.52, infeed_y + 0.52):
            infeed_parts.extend(extrusion_parts(0.075, 0.28, transform((leg_x, leg_y, 0.17))))
            infeed_parts.extend(levelling_foot_parts(transform((leg_x, leg_y, 0.0))))
    for brace_y in (infeed_y - 0.52, infeed_y + 0.52):
        infeed_parts.extend(
            extrusion_parts(
                0.055,
                0.88,
                transform((infeed_x, brace_y, 0.16), rpy=(0.0, math.pi / 2.0, 0.0)),
            )
        )
    # Mast and its guide, with the pallet magazine's top bracket.
    infeed_parts.extend(
        extrusion_parts((0.34, 0.34), 1.55, transform((infeed_x + 0.86, infeed_y, 0.76)), mat=MAT_STEEL)
    )
    infeed_parts.append(
        (
            chamfer_box((1.20, 0.10, 0.10), 0.008),
            transform((infeed_x - 0.62, infeed_y, 1.44)),
            MAT_BRUSHED,
        )
    )
    for guide_y in (infeed_y - 0.44, infeed_y + 0.44):
        infeed_parts.append(
            (
                chamfer_box((0.040, 0.040, 1.00), 0.005),
                transform((infeed_x - 0.52, guide_y, 0.95)),
                MAT_ALUMINUM,
            )
        )
    infeed_parts.append(
        (
            chamfer_cylinder(0.035, 0.42, sections=20),
            transform((infeed_x - 0.02, infeed_y, 1.20)),
            MAT_BRUSHED,
        )
    )
    scene.add(assembly_mesh(infeed_parts))
    # Empty pallets waiting in the magazine are the same pallets the line runs.
    stack_pallet = pallet_assembly_mesh()
    for stack_index in range(5):
        scene.add(
            stack_pallet,
            pose=transform((infeed_x, infeed_y, 0.435 + stack_index * 0.068)),
        )

    # Gearmotor drive units under the belt, one per conveyor section.
    for drive_y in (-9.60, 7.30):
        drive_parts = [
            (
                chamfer_box((0.24, 0.30, 0.26), 0.010),
                transform((0.53, drive_y, 0.255)),
                MAT_CABINET_TRIM,
            ),
            # Motor: a finned barrel with its terminal box and fan cowl.
            (
                chamfer_cylinder(0.088, 0.24, sections=28),
                transform((0.80, drive_y, 0.275), rpy=(0.0, math.pi / 2, 0.0)),
                MAT_BRUSHED,
            ),
            (
                chamfer_cylinder(0.070, 0.075, sections=24),
                transform((0.94, drive_y, 0.275), rpy=(0.0, math.pi / 2, 0.0)),
                MAT_DARK_METAL,
            ),
            (
                chamfer_box((0.09, 0.10, 0.075), 0.006),
                transform((0.80, drive_y, 0.425)),
                MAT_CABINET_TRIM,
            ),
            (
                chamfer_cylinder(0.030, 0.26, sections=18),
                transform((0.35, drive_y, 0.255), rpy=(0.0, math.pi / 2, 0.0)),
                MAT_STEEL,
            ),
            (
                trimesh.creation.cylinder(radius=0.016, height=0.55, sections=10),
                transform((0.72, drive_y, 0.10), rpy=(0.30, 0.0, 0.0)),
                MAT_HOSE,
            ),
        ]
        for fin_x in np.linspace(0.71, 0.89, 7):
            drive_parts.append(
                (
                    trimesh.creation.annulus(r_min=0.088, r_max=0.100, height=0.010, sections=24),
                    transform((fin_x, drive_y, 0.275), rpy=(0.0, math.pi / 2, 0.0)),
                    MAT_BRUSHED,
                )
            )
        drive_parts.extend(
            bolt_row_parts(
                [(0.53 + x, drive_y + y, 0.385) for x in (-0.09, 0.09) for y in (-0.12, 0.12)],
                0.016,
                0.010,
            )
        )
        scene.add(assembly_mesh(drive_parts))

    # The take-off deck starts clear of the conveyor's head pulley rather
    # than running into it, and the finished unit is picked off its middle.
    deck_start = CONVEYOR_Y_MAX + 0.45
    deck_length = 1.30
    deck_centre = deck_start + deck_length / 2.0
    outfeed_parts = [
        (
            chamfer_box((0.90, deck_length, 0.08), 0.008),
            transform((0.0, deck_centre, 0.36)),
            MAT_DARK_METAL,
        ),
        (
            chamfer_box((1.06, 0.09, 0.30), 0.008),
            transform((0.0, deck_start + deck_length - 0.06, 0.52)),
            MAT_ALUMINUM,
        ),
    ]
    for bumper_x in (-0.30, 0.30):
        outfeed_parts.append(
            (
                chamfer_cylinder(0.028, 0.055, sections=18),
                transform(
                    (bumper_x, deck_start + deck_length - 0.11, 0.52),
                    rpy=(math.pi / 2.0, 0.0, 0.0),
                ),
                MAT_HOSE,
            )
        )
    # Roller top on the take-off deck, matching the line it feeds from.
    lie_along_x = transform(rpy=(0.0, math.pi / 2.0, 0.0))
    deck_roller = chamfer_cylinder(0.022, 0.72, chamfer=0.004, sections=16)
    for roller_index in range(11):
        outfeed_parts.append(
            (
                deck_roller,
                transform((0.0, deck_start + 0.09 + roller_index * 0.112, 0.422)) @ lie_along_x,
                MAT_STEEL,
            )
        )
    for leg_x in (-0.36, 0.36):
        for leg_y in (deck_centre - 0.48, deck_centre + 0.48):
            outfeed_parts.extend(extrusion_parts(0.070, 0.28, transform((leg_x, leg_y, 0.18))))
            outfeed_parts.extend(levelling_foot_parts(transform((leg_x, leg_y, 0.0))))
    scene.add(assembly_mesh(outfeed_parts))


def finished_unit_mesh():
    """A closed junction box: what comes off the end of this line."""
    parts = [
        (chamfer_box((0.46, 0.64, 0.062), 0.008), transform((0.0, 0.0, -0.019)), MAT_BRUSHED),
        (fillet_box((0.42, 0.60, 0.040), 0.008), transform((0.0, 0.0, 0.030)), MAT_WHITE_SATIN),
        (
            chamfer_box((0.135, 0.095, 0.004), 0.002),
            transform((0.0, 0.15, 0.050)),
            MAT_WHITE,
        ),
    ]
    for latch_y in (-0.20, 0.20):
        parts.append(
            (
                chamfer_box((0.030, 0.055, 0.030), 0.005),
                transform((-0.235, latch_y, 0.010)),
                MAT_BLACK,
            )
        )
        parts.append(
            (
                chamfer_box((0.030, 0.055, 0.030), 0.005),
                transform((0.235, latch_y, 0.010)),
                MAT_BLACK,
            )
        )
    for port_y in (-0.24, 0.24):
        parts.append(
            (
                chamfer_box((0.070, 0.060, 0.055), 0.006),
                transform((0.245, port_y, 0.005)),
                MAT_HV_ORANGE,
            )
        )
    return assembly_mesh(parts)


def add_palletiser(scene):
    """Take-off robot and the stocker it stacks finished units into."""
    base_x, base_y, base_z = PALLETISER_BASE
    # Both ends of the transfer sit inside the arm's reach; the take-off point
    # is out on the deck of the outfeed rather than on its centreline, and the
    # set-down point is the near column of the top shelf.
    pick = np.array(PALLETISER_PICK)
    place = np.array(PALLETISER_PLACE)
    product = finished_unit_mesh()

    # Pedestal.
    pedestal_parts = [
        (
            chamfer_box((0.52, 0.52, 0.06), 0.008),
            transform((base_x, base_y, 0.03)),
            MAT_CABINET_TRIM,
        ),
        (
            chamfer_cylinder(0.17, base_z - 0.06, sections=48),
            transform((base_x, base_y, (base_z + 0.06) / 2.0)),
            MAT_WHITE_SATIN,
        ),
        (
            chamfer_cylinder(0.20, 0.05, sections=48),
            transform((base_x, base_y, base_z - 0.02)),
            MAT_BRUSHED,
        ),
        (
            chamfer_box((0.40, 0.50, 0.58), 0.010),
            transform((base_x + 0.02, base_y + 0.72, 0.29)),
            MAT_CABINET,
        ),
        (
            chamfer_box((0.026, 0.030, 0.20), 0.005),
            transform((base_x - 0.19, base_y + 0.72, 0.34)),
            MAT_BRUSHED,
        ),
        (
            chamfer_box((0.42, 0.52, 0.030), 0.006),
            transform((base_x + 0.02, base_y + 0.72, 0.595)),
            MAT_CABINET_TRIM,
        ),
    ]
    pedestal_parts.extend(
        bolt_row_parts(
            [(base_x + x, base_y + y, 0.060) for x in (-0.21, 0.21) for y in (-0.21, 0.21)],
            0.026,
            0.016,
        )
    )
    pedestal_parts.extend(bolt_circle_parts(8, 0.185, 0.017, 0.010, transform((base_x, base_y, base_z - 0.002))))
    for vent_z in np.linspace(0.12, 0.26, 5):
        pedestal_parts.append(
            (
                chamfer_box((0.010, 0.30, 0.014), 0.003),
                transform((base_x - 0.178, base_y + 0.72, vent_z)),
                MAT_DARK_METAL,
            )
        )
    scene.add(assembly_mesh(pedestal_parts))

    # Stocker: two columns of finished units, stacked three high on shelves.
    # The stacks are 0.64 deep on a 0.68 pitch, so the shelf has to be 1.40
    # deep to carry them; a shorter one leaves the units hanging over its lip.
    stocker_parts = []
    post_offset = 0.70
    shelf_deep = 1.44
    for post_x in (place[0] - 0.42, place[0] + 0.42):
        for post_y in (base_y - post_offset, base_y + post_offset):
            stocker_parts.extend(extrusion_parts(0.05, 1.34, transform((post_x, post_y, 0.67))))
            stocker_parts.extend(levelling_foot_parts(transform((post_x, post_y, 0.0)), plate=0.10))
    for shelf_z in STOCKER_SHELVES:
        wide = 0.94 if shelf_z > 0.9 else 0.92
        stocker_parts.append(
            (
                chamfer_box((wide, shelf_deep, 0.030), 0.005),
                transform((place[0], base_y, shelf_z)),
                MAT_BRUSHED,
            )
        )
        # Edge lip, and the rails the shelf is carried on.
        for lip_y in (
            base_y - shelf_deep / 2.0 + 0.012,
            base_y + shelf_deep / 2.0 - 0.012,
        ):
            stocker_parts.append(
                (
                    chamfer_box((wide, 0.024, 0.030), 0.004),
                    transform((place[0], lip_y, shelf_z + 0.028)),
                    MAT_ALUMINUM,
                )
            )
        for rail_x in (place[0] - 0.42, place[0] + 0.42):
            stocker_parts.extend(
                extrusion_parts(
                    0.04,
                    shelf_deep - 0.06,
                    transform(
                        (rail_x, base_y, shelf_z - 0.036),
                        rpy=(math.pi / 2.0, 0.0, 0.0),
                    ),
                )
            )
    stocker_parts.extend(extrusion_parts(0.10, 1.36, transform((place[0] + 0.42, base_y - post_offset, 0.68))))
    scene.add(assembly_mesh(stocker_parts))
    for shelf_z in STOCKER_SHELVES[:-1]:
        for stack_y in (base_y - 0.34, base_y + 0.34):
            for level in range(3):
                scene.add(
                    product,
                    pose=transform((place[0], stack_y, shelf_z + 0.07 + level * 0.105)),
                )
    # The near column of the top shelf is the one the robot is filling, so it
    # is drawn by the animation rather than here.
    for level in range(2):
        scene.add(
            product,
            pose=transform((place[0], base_y + 0.34, place[2] + level * 0.105)),
        )

    robot = UR15(scene, transform((base_x, base_y, base_z)))
    seed = np.array((0.9, -1.2, 1.9, -2.2, -1.6, 0.0))
    hold = np.array((1.6, -1.35, 1.75, -1.95, -1.6, 0.0))
    # Solve the working point first and seed its approach from it: seeded the
    # other way round the solver can pick a different elbow branch for the two
    # ends of the same move, and the arm swings through itself between them.
    at_pick, _ = solve_tool_pose(robot.base_pose, pick, seed)
    above_pick, _ = solve_tool_pose(robot.base_pose, pick + np.array((0.0, 0.0, 0.40)), at_pick)
    at_place, _ = solve_tool_pose(robot.base_pose, place, hold)
    above_place, _ = solve_tool_pose(robot.base_pose, place + np.array((0.0, 0.0, 0.34)), at_place)
    span = CYCLE_TIME
    keyframes = (
        (0.00 * span, above_pick, 0.0),
        (0.09 * span, above_pick, 0.0),
        (0.15 * span, at_pick, 0.0),
        (0.19 * span, at_pick, 1.0),
        (0.25 * span, above_pick, 1.0),
        (0.38 * span, above_place, 1.0),
        (0.45 * span, at_place, 1.0),
        (0.49 * span, at_place, 0.0),
        (0.56 * span, above_place, 0.0),
        (0.72 * span, above_pick, 0.0),
        (1.00 * span, above_pick, 0.0),
    )
    return Palletiser(
        robot=robot,
        keyframes=keyframes,
        carried_node=scene.add(product, pose=transform((0.0, 0.0, -10.0))),
        outfeed_node=scene.add(product, pose=transform(pick - (0, 0, 0.05))),
        stacked_node=scene.add(product, pose=transform(place)),
        outfeed_pose=transform(pick - np.array((0.0, 0.0, 0.05))),
        stacked_pose=transform(place),
    )


def update_palletiser(scene, palletiser, seconds):
    """Pick a finished unit off the take-off and set it on the stack."""
    phase = cycle_phase(seconds)
    frames = palletiser.keyframes
    joints, grip = frames[-1][1], frames[-1][2]
    for index in range(len(frames) - 1):
        t0, q0, g0 = frames[index]
        t1, q1, g1 = frames[index + 1]
        if phase <= t1:
            blend = smootherstep((phase - t0) / max(t1 - t0, 1e-6))
            joints = q0 * (1.0 - blend) + q1 * blend
            grip = g0 * (1.0 - blend) + g1 * blend
            break
    tool = palletiser.robot.update(joints, grip)
    carrying = frames[3][0] <= phase < frames[7][0]
    hidden = transform((0.0, 0.0, -10.0))
    scene.set_pose(
        palletiser.carried_node,
        pose=(tool @ transform((0.0, 0.0, GRIPPER_OBJECT_OFFSET)) if carrying else hidden),
    )
    # The slot on the stack is empty while its unit is in transit, and the
    # next finished unit slides onto the take-off before the cycle repeats.
    scene.set_pose(
        palletiser.stacked_node,
        pose=hidden if carrying else palletiser.stacked_pose,
    )
    arriving = smootherstep((phase - frames[8][0]) / max(frames[9][0] - frames[8][0], 1e-6))
    approach = palletiser.outfeed_pose.copy()
    approach[1, 3] -= (1.0 - arriving) * 1.05
    scene.set_pose(
        palletiser.outfeed_node,
        pose=hidden if frames[3][0] <= phase < frames[8][0] else approach,
    )


def add_ceiling(scene):
    """High-bay roof, trusses and the drops that carry the line lighting."""
    scene.add(
        box_mesh((FLOOR_WIDTH, FLOOR_DEPTH, 0.16), MAT_CEILING),
        pose=transform((0.0, FLOOR_CENTER_Y, CEILING_HEIGHT + 0.08)),
    )
    # Roof steel: chorded trusses on H-section columns. Rolled sections are
    # built as sections — a web with two flanges — because a plain bar reads
    # as scenery and a flanged one reads as structure.
    for truss_y in np.arange(-20.0, 32.1, 5.0):
        truss_parts = []
        for chord_z, chord_depth, chord_width in (
            (TRUSS_UPPER, 0.30, 0.16),
            (TRUSS_LOWER, 0.16, 0.12),
        ):
            truss_parts.append(
                (
                    chamfer_box((FLOOR_WIDTH, chord_width * 0.45, chord_depth), 0.008),
                    transform((0.0, truss_y, chord_z)),
                    MAT_TRUSS,
                )
            )
            for flange_z in (
                chord_z - chord_depth / 2.0 + 0.018,
                chord_z + chord_depth / 2.0 - 0.018,
            ):
                truss_parts.append(
                    (
                        chamfer_box((FLOOR_WIDTH, chord_width, 0.036), 0.006),
                        transform((0.0, truss_y, flange_z)),
                        MAT_TRUSS,
                    )
                )
        for web_x in np.arange(-12.0, 12.1, 1.6):
            truss_parts.append(
                (
                    chamfer_box((0.07, 0.07, TRUSS_UPPER - TRUSS_LOWER), 0.008),
                    transform((web_x, truss_y, (TRUSS_UPPER + TRUSS_LOWER) / 2.0)),
                    MAT_TRUSS,
                )
            )
            # Diagonal between every pair of verticals.
            if web_x < 12.0:
                truss_parts.append(
                    (
                        chamfer_box((0.05, 0.05, 1.78), 0.006),
                        transform(
                            (
                                web_x + 0.8,
                                truss_y,
                                (TRUSS_UPPER + TRUSS_LOWER) / 2.0,
                            ),
                            rpy=(0.0, math.radians(63.0), 0.0),
                        ),
                        MAT_TRUSS,
                    )
                )
        for column_x in (-12.6, 12.6):
            truss_parts.append(
                (
                    chamfer_box((0.34, 0.14, CEILING_HEIGHT), 0.012),
                    transform((column_x, truss_y, CEILING_HEIGHT / 2.0)),
                    MAT_TRUSS,
                )
            )
            for flange_x in (column_x - 0.15, column_x + 0.15):
                truss_parts.append(
                    (
                        chamfer_box((0.045, 0.34, CEILING_HEIGHT), 0.010),
                        transform((flange_x, truss_y, CEILING_HEIGHT / 2.0)),
                        MAT_TRUSS,
                    )
                )
            truss_parts.append(
                (
                    chamfer_box((0.60, 0.60, 0.05), 0.010),
                    transform((column_x, truss_y, 0.025)),
                    MAT_STEEL,
                )
            )
            truss_parts.append(
                (
                    chamfer_box((0.52, 0.52, 0.10), 0.010),
                    transform((column_x, truss_y, CEILING_HEIGHT - 0.05)),
                    MAT_TRUSS,
                )
            )
        scene.add(assembly_mesh(truss_parts))
    # Structures at eye level stop short of the camera; anything that ran the
    # full depth of the bay would smear across the frame.
    span = BAY_Y_MAX - BAY_Y_MIN
    center = (BAY_Y_MAX + BAY_Y_MIN) / 2.0
    # Everything that runs the length of the bay sits outside the orbit, so
    # the camera never flies through it.
    for purlin_x in (-12.0, -10.6, 10.6, 12.0):
        scene.add(
            rounded_box_mesh((0.12, span, 0.22), MAT_TRUSS, 0.010),
            pose=transform((purlin_x, center, TRUSS_LOWER - 0.22)),
        )
    for tray_x in (-11.3, 11.3):
        tray_parts = [
            (
                chamfer_box((0.44, span, 0.05), 0.008),
                transform((tray_x, center, 4.62)),
                MAT_DUCT,
            )
        ]
        for rail_offset in (-0.21, 0.21):
            tray_parts.append(
                (
                    chamfer_box((0.03, span, 0.11), 0.005),
                    transform((tray_x + rail_offset, center, 4.67)),
                    MAT_DUCT,
                )
            )
        for hanger_y in np.arange(BAY_Y_MIN + 1.0, BAY_Y_MAX, 2.5):
            tray_parts.append(
                (
                    chamfer_cylinder(0.014, TRUSS_LOWER - 4.7, sections=12),
                    transform((tray_x, hanger_y, (TRUSS_LOWER + 4.7) / 2.0 - 0.11)),
                    MAT_BRUSHED,
                )
            )
            tray_parts.append(
                (
                    chamfer_box((0.50, 0.030, 0.035), 0.005),
                    transform((tray_x, hanger_y, 4.68)),
                    MAT_BRUSHED,
                )
            )
        scene.add(assembly_mesh(tray_parts))


def add_line_lighting(scene):
    """Continuous-row LED fixtures suspended over the line."""
    rail_span = LIGHT_Y_MAX - LIGHT_Y_MIN
    rail_centre = (LIGHT_Y_MAX + LIGHT_Y_MIN) / 2.0
    for rail_x in (-2.7, -0.9, 0.9, 2.7):
        rail_parts = [
            (
                chamfer_box((0.06, rail_span, 0.090), 0.006),
                transform((rail_x, rail_centre, LIGHT_HEIGHT + 0.12)),
                MAT_TRUSS,
            )
        ]
        for hanger_y in np.arange(LIGHT_Y_MIN + 1.4, LIGHT_Y_MAX, 4.0):
            rail_parts.append(
                (
                    chamfer_cylinder(0.011, TRUSS_LOWER - LIGHT_HEIGHT - 0.3, sections=10),
                    transform(
                        (
                            rail_x,
                            hanger_y,
                            (TRUSS_LOWER + LIGHT_HEIGHT) / 2.0 - 0.02,
                        )
                    ),
                    MAT_BRUSHED,
                )
            )
            rail_parts.append(
                (
                    chamfer_box((0.075, 0.045, 0.030), 0.005),
                    transform((rail_x, hanger_y, LIGHT_HEIGHT + 0.175)),
                    MAT_BRUSHED,
                )
            )
        scene.add(assembly_mesh(rail_parts))
    # The rows flank the line rather than sitting on its centreline, so the
    # conveyor stays visible when the camera looks straight down the bay.
    for fixture_x in (-1.9, 1.9):
        for start in np.arange(LIGHT_Y_MIN + 0.5, LIGHT_Y_MAX - 2.4, 2.60):
            length = 2.42
            center_y = start + length / 2.0
            fixture_parts = [
                (
                    chamfer_box((0.155, length, 0.095), 0.008),
                    transform((fixture_x, center_y, LIGHT_HEIGHT)),
                    MAT_WHITE,
                ),
                (
                    chamfer_box((0.125, length - 0.10, 0.022), 0.004),
                    transform((fixture_x, center_y, LIGHT_HEIGHT - 0.055)),
                    MAT_LENS,
                ),
            ]
            for cap_offset in (-length / 2.0, length / 2.0):
                fixture_parts.append(
                    (
                        chamfer_box((0.16, 0.03, 0.10), 0.006),
                        transform((fixture_x, center_y + cap_offset, LIGHT_HEIGHT)),
                        MAT_CABINET_TRIM,
                    )
                )
            # Suspension brackets and the through-wiring between fixtures.
            for bracket_offset in (-length / 2.0 + 0.30, length / 2.0 - 0.30):
                fixture_parts.append(
                    (
                        chamfer_box((0.075, 0.030, 0.055), 0.005),
                        transform(
                            (
                                fixture_x,
                                center_y + bracket_offset,
                                LIGHT_HEIGHT + 0.070,
                            )
                        ),
                        MAT_CABINET_TRIM,
                    )
                )
            fixture_parts.append(
                (
                    trimesh.creation.cylinder(radius=0.009, height=0.18, sections=10),
                    transform(
                        (fixture_x, center_y + length / 2.0 + 0.09, LIGHT_HEIGHT + 0.02),
                        rpy=(math.pi / 2.0, 0.0, 0.0),
                    ),
                    MAT_HOSE,
                )
            )
            scene.add(assembly_mesh(fixture_parts))


def add_lights(scene):
    # A roofed bay is lit from its own fixtures, so the light sits under the
    # roof rather than outside the building. Exactly one spot casts shadows:
    # its cone has to reach the whole visible floor, because pyrender leaves
    # everything outside a shadow cone hard-edged and unlit, and every extra
    # shadow caster costs a full scene pass per frame.
    scene.add(
        pyrender.SpotLight(
            color=np.array((0.96, 1.0, 0.99)),
            intensity=540.0 * LIGHT_LEVEL,
            innerConeAngle=0.55,
            outerConeAngle=1.27,
        ),
        pose=look_at(
            (ORBIT_CENTRE[0] + 1.30, ORBIT_CENTRE[1] + 0.90, 6.85),
            (ORBIT_CENTRE[0], ORBIT_CENTRE[1], 0.40),
        ),
    )
    for y in np.arange(CONVEYOR_Y_MIN + 1.5, CONVEYOR_Y_MAX, 3.2):
        scene.add(
            pyrender.PointLight(
                color=np.array((0.82, 0.91, 0.95)),
                intensity=15.0 * LIGHT_LEVEL,
            ),
            pose=transform((0.0, y, 3.02)),
        )
    for side in (-1.0, 1.0):
        for y in (CELL_Y_START - 1.0, CELL_Y_START + 8.0):
            scene.add(
                pyrender.PointLight(
                    color=np.array((0.72, 0.82, 0.88)),
                    intensity=30.0 * LIGHT_LEVEL,
                ),
                pose=transform((side * 5.6, y, 4.55)),
            )


class YokePose(np.ndarray):
    """Joint values already measured on the yoke mounting.

    Every other pose in this file is a hand-tuned value from the flat T
    mounting and is retargeted onto the yoke by tool pose. That works while
    the tool pose is the whole specification, and it fails when the shape of
    the arm is the point: the solver keeps the tool and picks whatever elbow
    branch it likes, which for the folded carry pose is the one that puts the
    forearm through the column. Poses of this type are passed through.
    """

    @classmethod
    def of(cls, values):
        return np.asarray(values, dtype=float).view(cls)


# Compact, non-crossing task poses. The right arm is always derived as the
# exact kinematic mirror of the left arm.
L_HOME = np.array((-3.1514, -1.0208, 2.7739, -1.7531, 1.5610, -1.5708))
L_STOCK_HIGH = np.array((-2.1232, -0.6695, 1.4346, -0.7651, 2.5892, -1.5708))
L_STOCK = np.array((-2.1607, -0.3059, 0.6022, -0.2964, 2.5517, -1.5708))

L_TASK_POSES = {
    "housing_load": np.array((-2.3462, -0.5757, 1.3564, -0.8949, 2.0210, -1.5708)),
    "connector_insert": np.array((-2.5159, -0.7476, 1.6218, -0.8741, 2.1965, -1.5708)),
    "main_route": np.array((-2.3556, -0.6411, 1.4707, -0.8899, 2.0776, -1.5708)),
    "branch_route": np.array((-2.3218, -0.4487, 1.2093, -0.8837, 1.9405, -1.5708)),
    "clip_seat": np.array((-2.3721, -0.4770, 1.2912, -0.8863, 1.9854, -1.5708)),
    "strain_relief": np.array((-2.3334, -0.5649, 1.3797, -0.8912, 2.0251, -1.5708)),
    "cover_place": np.array((-2.2506, -0.6559, 1.5254, -0.8823, 2.0750, -1.5708)),
    "latch_press": np.array((-2.3529, -0.4514, 1.2142, -0.8843, 1.9484, -1.5708)),
    "electrical_test": np.array((-2.3266, -0.5385, 1.3465, -0.8907, 2.0069, -1.5708)),
    "vision_inspect": np.array((-2.1527, -0.7522, 1.6590, -0.8657, 2.1139, -1.5708)),
}
L_TASK_HIGH_POSES = {
    "housing_load": np.array((-2.1614, -0.7493, 1.6440, -0.8449, 2.1105, -1.5708)),
    "connector_insert": np.array((-2.3265, -0.9288, 1.9186, -0.8071, 2.3036, -1.5708)),
    "main_route": np.array((-2.1641, -0.8073, 1.7453, -0.8373, 2.1603, -1.5708)),
    "branch_route": np.array((-2.1425, -0.6248, 1.5105, -0.8360, 2.0317, -1.5708)),
    "clip_seat": np.array((-2.1923, -0.6521, 1.5946, -0.8328, 2.0796, -1.5708)),
    "strain_relief": np.array((-2.1465, -0.7305, 1.6589, -0.8413, 2.1076, -1.5708)),
    "cover_place": np.array((-2.0490, -0.7964, 1.7601, -0.8373, 2.1292, -1.5708)),
    "latch_press": np.array((-2.1752, -0.6334, 1.5254, -0.8335, 2.0465, -1.5708)),
    "electrical_test": np.array((-2.1412, -0.7045, 1.6280, -0.8416, 2.0897, -1.5708)),
    "vision_inspect": np.array((-1.9350, -0.8692, 1.8499, -0.8271, 2.1395, -1.5708)),
}


def mirror_joint_pose(joints):
    return np.array(
        (
            -joints[0],
            math.pi - joints[1],
            -joints[2],
            math.pi - joints[3],
            -joints[4],
            -joints[5],
        )
    )


R_HOME = mirror_joint_pose(L_HOME)
# The pose the cell turns in, with a part held between both hands. The old
# home pose stood the elbows over two metres up and left the part hanging on
# the column; this one folds the elbows down and holds the part out in front,
# clear of the column and of the stereo head. It is measured on the yoke, so
# it is a YokePose and the retargeting leaves it alone.
L_TURN = YokePose.of((-3.4927, 0.3103, 2.9501, -2.4881, 0.9986, -1.8063))
R_TURN = YokePose.of(mirror_joint_pose(L_TURN))


def task_joint_pose(operation, side, high=False):
    pose = L_TASK_HIGH_POSES[operation] if high else L_TASK_POSES[operation]
    return pose if side == "left" else mirror_joint_pose(pose)


def pick_keyframes(cell_index, side, keep_tool, standby, timing):
    """Fetch the next component from the stocker while a pallet transfers."""
    if not fetches_component(cell_index):
        # Test and inspection heads simply hold clear above their station.
        return [
            (0.0, standby, 1.0),
            (timing["ready"] - 0.55 * PACE, standby, 1.0),
        ]
    turn = L_TURN if side == "left" else R_TURN
    if keep_tool:
        # A press station keeps its tool, so there is nothing to collect.
        return [(0.0, turn, 1.0), (timing["hold"], turn, 1.0)]
    stock_high = L_STOCK_HIGH if side == "left" else mirror_joint_pose(L_STOCK_HIGH)
    stock = L_STOCK if side == "left" else mirror_joint_pose(L_STOCK)
    shift = timing["shift"]
    return [
        (0.0, turn, 0.0),
        (timing["back_time"], turn, 0.0),
        (STOCK_REACH + shift, stock_high, 0.0),
        (STOCK_CONTACT + shift, stock, 0.0),
        (STOCK_GRASP + shift, stock, 1.0),
        (STOCK_CLEAR + shift, stock_high, 1.0),
        (timing["out_start"], turn, 1.0),
        (timing["hold"], turn, 1.0),
    ]


def legacy_base_pose(side):
    """The flat T mounting the work poses were originally tuned against."""
    sign = -1.0 if side == "left" else 1.0
    return transform(
        (sign * SHOULDER_SPAN / 2.0, 0.0, SHOULDER_HEIGHT),
        rpy=(0.0, sign * math.pi / 2.0, 0.0),
    )


def yoke_base_pose(side):
    """The angled Y mounting actually built into the cell."""
    sign = -1.0 if side == "left" else 1.0
    return transform(
        (sign * YOKE_SPREAD, 0.0, SHOULDER_HEIGHT + YOKE_RISE),
        rpy=(0.0, sign * (math.pi / 2.0 - YOKE_ANGLE), 0.0),
    )


@cache
def retarget_joints(key, side):
    """Joints that put the tool where the flat mounting used to put it."""
    legacy = np.array(key, dtype=float)
    _, target = UR15.forward(legacy_base_pose(side), legacy)
    base = yoke_base_pose(side)

    def residual(joints):
        _, tool = UR15.forward(base, joints)
        offset = tool[:3, 3] - target[:3, 3]
        turn = Rotation.from_matrix(tool[:3, :3] @ target[:3, :3].T).as_rotvec()
        return np.concatenate((offset * 4.0, turn))

    solved = least_squares(residual, legacy, xtol=1e-13, ftol=1e-13, gtol=1e-13)
    return tuple(solved.x), float(np.linalg.norm(solved.fun))


def stock_pick_local(side):
    """Where the gripper actually meets the tray on the yoke mounting.

    Every working pose retargets exactly, but the deep reach into the stocker
    lands a few centimetres away, so the tray is placed against the reach
    rather than the reach being forced onto the tray.
    """
    legacy = L_STOCK if side == "left" else mirror_joint_pose(L_STOCK)
    joints = np.array(retarget_joints(tuple(np.round(legacy, 7)), side)[0])
    _, tool = UR15.forward(yoke_base_pose(side), joints)
    return tool @ transform((0.0, 0.0, GRIPPER_OBJECT_OFFSET))


def solve_tool_pose(base_pose, position, seed, yaw=0.0, orientation=None):
    """Joints that put the tool at a point, pointing straight down.

    Pass `orientation` to keep a wrist that is already right and move only the
    point it works at — a hand-tuned station pose approaches the product at
    its own angle, and forcing it upright would throw that away.
    """
    target = np.eye(4)
    target[:3, :3] = (
        Rotation.from_euler("xyz", (math.pi, 0.0, yaw)).as_matrix()
        if orientation is None
        else np.asarray(orientation, dtype=float)
    )
    target[:3, 3] = np.asarray(position, dtype=float)

    def residual(joints):
        _, tool = UR15.forward(base_pose, joints)
        turn = Rotation.from_matrix(tool[:3, :3] @ target[:3, :3].T).as_rotvec()
        return np.concatenate(((tool[:3, 3] - target[:3, 3]) * 4.0, turn))

    solved = least_squares(residual, np.asarray(seed, dtype=float))
    return solved.x, float(np.linalg.norm(solved.fun))


def look_pose(base_pose, position, seed):
    """Joints that put the head at a point, looking as near straight down as
    the reach allows. The far corner of a product is only reachable with the
    head leaning over it, which is what a camera on an arm does anyway."""
    down = np.array((0.0, 0.0, -1.0))

    def residual(joints):
        _, tool = UR15.forward(base_pose, joints)
        # Stay near the pose it came from: without this the solver is free to
        # roll the wrist a quarter turn between two neighbouring points on the
        # same lane, and the head spins on its way across the product.
        return np.concatenate(
            (
                (tool[:3, 3] - position) * 8.0,
                (tool[:3, 2] - down) * 0.6,
                (joints - seed) * 0.30,
            )
        )

    solved = least_squares(residual, seed, xtol=1e-13, ftol=1e-13)
    _, tool = UR15.forward(base_pose, solved.x)
    return solved.x, float(np.linalg.norm(tool[:3, 3] - position))


@cache
def inspection_scan(side):
    """A raster across the whole product for the visual inspection head.

    The joint-space nudge the other stations sweep with moves the tool about
    50 mm, which over a 0.72 m product reads as a head parked above it. This
    is built in the cell's own frame instead: two lanes down the length of
    the product, joined at the far end.
    """
    base = yoke_base_pose(side)
    seed = np.array(retarget_joints(tuple(np.round(task_joint_pose("vision_inspect", side), 7)), side)[0])
    along = (-0.34, -0.17, 0.0, 0.17, 0.34)
    path = [(along[0], -0.80, 1.30)]
    path += [(x, -0.80, 1.14) for x in along]
    path.append((0.34, -0.90, 1.20))
    path += [(x, -1.00, 1.17) for x in reversed(along)]
    # Lift clear on the same lane before handing back to the ready pose,
    # rather than snapping across to it from down on the product.
    path.append((along[0], -1.00, 1.34))
    poses = []
    previous = seed
    for point in path:
        joints, _ = look_pose(base, np.array(point), previous)
        poses.append(YokePose.of(joints))
        previous = joints
    return tuple(poses)


# Where a latch sits on the product, in the cell's own frame: one on each
# side of the lid seam, which is the point the pallet's own copy takes.
LATCH_POINT = (0.22, -0.93, 0.735)
LATCH_CLEAR = 0.13


@cache
def latch_press_points(side):
    """Clear and contact poses for a latch head, built on the product.

    The joint-space step the other press station walks a fastener row with
    moves this pose 0.16 m down and only 0.04 m along, so the stroke drove
    the whole hand 0.23 m through the cover instead of setting a latch on
    it. There is one latch per arm, so each head works its own point and the
    wrist keeps the angle the station pose was tuned with.
    """
    base = yoke_base_pose(side)
    seed = np.array(retarget_joints(tuple(np.round(task_joint_pose("latch_press", side), 7)), side)[0])
    _, tool = UR15.forward(base, seed)
    hold = tool[:3, :3]
    reach = hold @ np.array((0.0, 0.0, GRIPPER_OBJECT_OFFSET))
    x = -LATCH_POINT[0] if side == "left" else LATCH_POINT[0]
    contact = np.array((x, LATCH_POINT[1], LATCH_POINT[2])) - reach
    poses = []
    previous = seed
    for point in (
        contact + np.array((0.0, 0.0, LATCH_CLEAR)),
        contact,
    ):
        joints, _ = solve_tool_pose(base, point, previous, orientation=hold)
        poses.append(YokePose.of(joints))
        previous = joints
    return tuple(poses)


def stock_pick_points(cell_index):
    """World positions where this cell's two grippers meet their trays."""
    root = initial_cell_root(cell_index)
    return [(root @ stock_pick_local(side))[:3, 3] for side in ("left", "right")]


def retarget_frames(frames, side):
    return [
        (
            moment,
            np.asarray(pose, dtype=float)
            if isinstance(pose, YokePose)
            else np.array(retarget_joints(tuple(np.round(pose, 7)), side)[0]),
            grip,
        )
        for moment, pose, grip in frames
    ]


# Joint-space directions used to build work points on the product: one that
# walks the tool along the part, and a wrist roll used for tug tests.
ALONG_DELTA = np.array((0.075, -0.025, 0.020, 0.005, -0.055, 0.0))
TWIST_DELTA = np.array((0.0, 0.0, 0.0, 0.0, 0.0, 0.26))
SEAT_DEPTH = {
    "housing_load": 0.07,
    "connector_insert": 0.16,
    "main_route": 0.05,
    "branch_route": 0.05,
    "clip_seat": 0.16,
    "strain_relief": 0.10,
    "cover_place": 0.09,
    "latch_press": 0.18,
    "electrical_test": 0.13,
    "vision_inspect": 0.00,
}


def arm_keyframes(cell_index, side):
    operation = CELL_OPERATIONS[cell_index]
    style, _, span, extra = station_work(operation)
    phases = STATION_PHASES[cell_index]
    start = phases["start"]
    seat = phases["seat"]
    release = phases["release"]
    finish = phases["finish"]
    timing = cell_timing(cell_index)
    turn = L_TURN if side == "left" else R_TURN
    high = task_joint_pose(operation, side, high=True)
    task = task_joint_pose(operation, side)
    # A station keeps its tool only if it has nothing to fetch. Latch press
    # installs the latches, so it collects one from its stocker like any
    # other component station; the two inspection heads never let go.
    keep_tool = operation in ("electrical_test", "vision_inspect")
    released_grip = 1.0 if keep_tool else 0.0
    # Between pallets a picking cell folds back over its table; a fixed-tool
    # head just lifts a little further clear of the passing product.
    standby = turn if fetches_component(cell_index) else high + (high - task) * 0.45
    prefix = pick_keyframes(cell_index, side, keep_tool, standby, timing)

    # Continue past the nominal contact pose to make insertion and seating
    # visible. The small back-off after contact reads as a controlled press,
    # rather than a component simply being placed on top.
    seated = task + (task - high) * SEAT_DEPTH[operation]

    def shifted(base, delta, distance):
        step = delta * distance
        return base + (step if side == "left" else -step)

    def lifted(fraction, distance=0.0):
        return shifted(task + (high - task) * fraction, ALONG_DELTA, distance)

    # The two arms of a cell are not driven from one program: the second one
    # trails and works a slightly shorter stroke. Where they carry a part
    # together they stay in step until it is released.
    trail = 0.0 if side == "left" else 0.10 * PACE
    carried = style == "place"
    work_lag = 0.0 if carried else trail

    frames = list(prefix)
    frames.append((timing["ready"], high, 1.0))
    frames.append((start + work_lag, high, 1.0))

    if style == "place":
        frames += [
            (start + span * 0.30, lifted(0.45), 1.0),
            (start + span * 0.54, task, 1.0),
            (seat, seated, 1.0),
            (release, seated, released_grip),
            # Once the part is free the arms separate: one taps its corner
            # home while the other is already lifting away.
            (
                release + (finish - release) * 0.28 + trail,
                shifted(seated, ALONG_DELTA, 0.55 if side == "left" else 0.0),
                released_grip,
            ),
            (release + (finish - release) * 0.62 + trail, lifted(0.5), released_grip),
            (finish + trail, high, released_grip),
        ]
    elif style == "insert":
        frames += [
            (start + span * 0.24 + work_lag, lifted(0.5), 1.0),
            (start + span * 0.40 + work_lag, task, 1.0),
            (start + span * 0.52 + work_lag, seated, 1.0),
            # Back off and twist: a seating check, not a single push.
            (start + span * 0.62 + work_lag, shifted(task, TWIST_DELTA, 0.5), 1.0),
            (seat + work_lag, seated, 1.0),
            (release + work_lag, seated, released_grip),
            (start + span * 0.86 + work_lag, lifted(0.55), released_grip),
            (finish + work_lag, high, released_grip),
        ]
    elif style == "sweep":
        frames += [
            (start + span * 0.18 + work_lag, lifted(0.40, 1.00), 1.0),
            (start + span * 0.34 + work_lag, shifted(task, ALONG_DELTA, 0.85), 1.0),
            (start + span * 0.50 + work_lag, shifted(seated, ALONG_DELTA, 0.25), 1.0),
            (seat + work_lag, seated, 1.0),
            (start + span * 0.72 + work_lag, shifted(seated, ALONG_DELTA, -0.50), 1.0),
            (release + work_lag, shifted(task, ALONG_DELTA, -0.95), released_grip),
            (start + span * 0.92 + work_lag, lifted(0.50, -0.60), released_grip),
            (finish + work_lag, high, released_grip),
        ]
    elif style == "press" and operation == "latch_press":
        strokes = int(extra)
        # One latch each, tapped home on the point it will sit on, with the
        # hand staying above the cover the whole time.
        clear, contact = latch_press_points(side)
        begin = start + span * 0.20 + work_lag
        stroke = (seat + work_lag - begin) / strokes
        frames.append((begin, clear, 1.0))
        cursor = begin
        for index in range(strokes):
            frames.append((cursor + stroke * 0.55, contact, 1.0))
            if index < strokes - 1:
                frames.append((cursor + stroke * 0.85, clear, 1.0))
            cursor += stroke
        frames += [
            (release + work_lag, contact, released_grip),
            (start + span * 0.88 + work_lag, clear, released_grip),
            (finish + work_lag, high, released_grip),
        ]
    elif style == "press":
        strokes = int(extra)
        # Each stroke lands on its own fastener, and the second arm works the
        # row from the far end.
        spots = [1.0 - 2.0 * index / max(strokes - 1, 1) for index in range(strokes)]
        if side == "right":
            spots.reverse()
        begin = start + span * 0.20 + work_lag
        stroke = (seat + work_lag - begin) / (strokes - 0.30)
        frames.append((begin, lifted(0.45, spots[0]), 1.0))
        cursor = begin
        for index, spot in enumerate(spots):
            frames.append((cursor + stroke * 0.42, shifted(task, ALONG_DELTA, spot), 1.0))
            frames.append((cursor + stroke * 0.70, shifted(seated, ALONG_DELTA, spot), 1.0))
            if index < strokes - 1:
                frames.append(
                    (
                        cursor + stroke * 1.00,
                        lifted(0.32, (spot + spots[index + 1]) / 2.0),
                        1.0,
                    )
                )
            cursor += stroke
        frames += [
            (release + work_lag, shifted(seated, ALONG_DELTA, spots[-1]), released_grip),
            (start + span * 0.88 + work_lag, lifted(0.55, spots[-1]), released_grip),
            (finish + work_lag, high, released_grip),
        ]
    elif style == "probe":
        # Two measurement points, each held still while the reading is taken.
        first, second = (0.62, -0.62) if side == "left" else (-0.62, 0.62)
        frames += [
            (start + span * 0.18 + work_lag, lifted(0.50, first), 1.0),
            (start + span * 0.34 + work_lag, shifted(task, ALONG_DELTA, first), 1.0),
            (seat + work_lag, shifted(seated, ALONG_DELTA, first), 1.0),
            (seat + extra * 0.42 + work_lag, shifted(seated, ALONG_DELTA, first), 1.0),
            (seat + extra * 0.56 + work_lag, lifted(0.30, first), 1.0),
            (seat + extra * 0.70 + work_lag, shifted(task, ALONG_DELTA, second), 1.0),
            (seat + extra * 0.80 + work_lag, shifted(seated, ALONG_DELTA, second), 1.0),
            (release + work_lag, shifted(seated, ALONG_DELTA, second), 1.0),
            (release + (finish - release) * 0.45 + work_lag, lifted(0.55, second), 1.0),
            (finish + work_lag, high, 1.0),
        ]
    else:
        # One head over the whole product: two lanes down its length, joined
        # at the far end, at the pace of a scan.
        path = inspection_scan(side)
        for index, pose in enumerate(path):
            fraction = 0.06 + 0.80 * index / (len(path) - 1)
            frames.append((start + span * fraction + work_lag, pose, 1.0))
        frames.append((finish + work_lag, high, 1.0))

    frames.append((finish + trail + 0.26 * PACE, standby, released_grip))
    frames.append((CYCLE_TIME, standby, released_grip))
    return tuple(retarget_frames(frames, side))


def smootherstep(value):
    value = float(np.clip(value, 0.0, 1.0))
    return value**3 * (value * (value * 6.0 - 15.0) + 10.0)


def cycle_phase(seconds):
    """Position inside the station cycle, in seconds."""
    return math.fmod(max(0.0, seconds), CYCLE_TIME)


def index_progress(seconds):
    """Pallet travel measured in station pitches."""
    seconds = max(0.0, seconds)
    completed = math.floor(seconds / CYCLE_TIME)
    phase = seconds - completed * CYCLE_TIME
    return completed + smootherstep(phase / INDEX_TIME)


def clamp_lift(seconds):
    """Lift-and-clamp stroke that seats a pallet on its locating pins."""
    phase = cycle_phase(seconds)
    raised = smootherstep((phase - INDEX_TIME) / CLAMP_TIME)
    lowered = smootherstep((phase - WORK_END) / RELEASE_TIME)
    return CLAMP_RISE * max(0.0, raised - lowered)


def stopper_extension(seconds):
    """Blade stroke of the pneumatic stopper in front of each station."""
    phase = cycle_phase(seconds)
    raised = smootherstep((phase - (INDEX_TIME - 0.80 * PACE)) / (0.26 * PACE))
    lowered = smootherstep((phase - WORK_END) / RELEASE_TIME)
    return STOPPER_STROKE * max(0.0, raised - lowered)


def motion_at(seconds, side, cell_index):
    phase = cycle_phase(seconds)
    keyframes = arm_keyframes(cell_index, side)
    for index in range(len(keyframes) - 1):
        t0, q0, g0 = keyframes[index]
        t1, q1, g1 = keyframes[index + 1]
        if phase <= t1:
            blend = smootherstep((phase - t0) / max(t1 - t0, 1e-6))
            return q0 * (1.0 - blend) + q1 * blend, g0 * (1.0 - blend) + g1 * blend
    return keyframes[-1][1], keyframes[-1][2]


def torso_yaw(seconds, initial_yaw, turns, timing):
    """Turn the table to the stocker while a pallet transfers, then back."""
    if not turns:
        return initial_yaw + math.pi
    phase = cycle_phase(seconds)
    turn_back = smootherstep(phase / timing["back_time"])
    turn_out = smootherstep((phase - timing["out_start"]) / timing["out_time"])
    return initial_yaw + math.pi * (1.0 - turn_back + turn_out)


def lift_height(seconds, turns, timing):
    """Raise the arms clear of the line for each table turn."""
    if not turns:
        return 0.0
    phase = cycle_phase(seconds)
    ramp = 0.24 * PACE
    # The table is already turning back as the cycle rolls over, so the lift
    # is up at phase zero and has to rise again at the end of the cycle.
    holds_from_previous = 1.0 - smootherstep((phase - timing["back_time"]) / ramp)
    rises_for_next = smootherstep((phase - (CYCLE_TIME - ramp)) / ramp)
    outbound = smootherstep((phase - (timing["out_start"] - ramp)) / ramp) - smootherstep(
        (phase - timing["ready"]) / ramp
    )
    return LIFT_TRAVEL * max(
        holds_from_previous,
        rises_for_next,
        max(0.0, outbound),
    )


def add_hud(image, seconds):
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    title = ImageFont.truetype(FONT_MONO, 16)
    label = ImageFont.truetype(FONT_MONO, 12)
    micro = ImageFont.truetype(FONT_MONO, 10)
    green = (154, 235, 189, 235)
    cyan = (137, 217, 235, 225)
    pale = (226, 238, 233, 220)
    muted = (165, 180, 174, 180)

    draw.rounded_rectangle(
        (42, 38, 430, 116),
        8,
        fill=(3, 12, 9, 165),
        outline=(126, 208, 160, 65),
    )
    draw.text((62, 53), "UR15 LINE  /  EV HARNESS ASSEMBLY", font=title, fill=pale)
    draw.text((62, 83), "10 ARMS  •  05 LIFT / ROTARY CELLS", font=label, fill=green)
    draw.ellipse((400, 82, 408, 90), fill=green)

    phase = "RESET"
    batch = 247
    rotation = 0.0
    progress = 0.04
    rotation = math.degrees(torso_yaw(seconds, 0, CELL_LAYOUT[0][2])) % 360.0
    if seconds < 1.8:
        phase, progress = "STOCK APPROACH", 0.10 + seconds / 1.8 * 0.15
    elif seconds < 3.4:
        phase, progress = "PICK FROM STOCK", 0.25 + (seconds - 1.8) / 1.6 * 0.18
    elif seconds < 6.2:
        phase, progress = "LIFT / ROTATE", 0.43 + (seconds - 3.4) / 2.8 * 0.22
    elif seconds < 7.9:
        phase, progress = "ASSEMBLE", 0.65 + (seconds - 6.2) / 1.7 * 0.16
    elif seconds < 10.2:
        phase, progress = "COMPLETE 360°", 0.81 + (seconds - 7.9) / 2.3 * 0.16
    elif seconds < 11.0:
        phase, progress = "RETURN", 1.0

    draw.rounded_rectangle(
        (42, 606, 454, 677),
        8,
        fill=(3, 12, 9, 165),
        outline=(126, 208, 160, 55),
    )
    draw.text((62, 620), f"BATCH {batch:04d}", font=label, fill=muted)
    draw.text((168, 620), phase, font=label, fill=green)
    draw.text((366, 620), f"{rotation:03.0f}°", font=label, fill=pale)
    draw.rounded_rectangle((62, 652, 434, 657), 3, fill=(68, 83, 77, 170))
    draw.rounded_rectangle((62, 652, 62 + 372 * progress, 657), 3, fill=green)

    # Line monitor: stockers, rotating upper bodies, and conveyor are online.
    panel = (1022, 38, 1238, 151)
    draw.rounded_rectangle(
        panel,
        8,
        fill=(3, 12, 9, 155),
        outline=(126, 208, 160, 50),
    )
    draw.text((1041, 52), "LINE STATUS", font=micro, fill=muted)
    for row, (cell, load, color) in enumerate((("STOCK", 92, green), ("LIFT", 96, cyan), ("BELT", 89, green))):
        y = 78 + row * 22
        draw.text((1041, y), cell, font=micro, fill=pale)
        draw.rounded_rectangle((1100, y + 3, 1194, y + 8), 2, fill=(60, 77, 71, 170))
        draw.rounded_rectangle((1100, y + 3, 1100 + load * 0.94, y + 8), 2, fill=color)
        draw.ellipse((1209, y + 1, 1217, y + 9), fill=color)

    draw.text(
        (1007, 684),
        "ILLUSTRATIVE — NOT TRAINING DATA",
        font=micro,
        fill=(190, 202, 197, 150),
    )
    image = Image.alpha_composite(image, overlay)
    return image.convert("RGB")


def grade(image, depth):
    array = np.asarray(image, dtype=np.float32) / 255.0
    # Filmic contrast with a restrained green/cyan split tone.
    array = np.clip((array - 0.5) * 1.08 + 0.5, 0.0, 1.0)
    array[..., 0] *= 0.96
    array[..., 1] *= 1.025
    array[..., 2] *= 1.01

    # Aerial perspective: the far end of the bay dissolves into haze rather
    # than ending on a hard black horizon.
    haze = np.where(depth > 0.0, depth, FOG_START + FOG_RANGE * 2.0)
    fog = np.clip((haze - FOG_START) / FOG_RANGE, 0.0, 1.0)[..., None] * FOG_MAX
    array = array * (1.0 - fog) + FOG_COLOUR * fog

    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    radius = ((xx - WIDTH * 0.5) / (WIDTH * 0.74)) ** 2 + ((yy - HEIGHT * 0.47) / (HEIGHT * 0.82)) ** 2
    vignette = np.clip(1.05 - radius * 0.26, 0.73, 1.0)[..., None]
    array *= vignette
    base = Image.fromarray(np.uint8(np.clip(array, 0, 1) * 255), "RGB")

    # A restrained depth-of-field pass keeps the robot crisp while gently
    # separating it from the workcell background.
    distance = np.where(depth > 0.0, depth, 8.0)
    defocus = np.clip((np.abs(distance - 9.50) - 1.80) / 4.5, 0.0, 0.38)
    defocus_mask = Image.fromarray(np.uint8(defocus * 255), "L").filter(ImageFilter.GaussianBlur(2.0))
    soft = base.filter(ImageFilter.GaussianBlur(2.4))
    base = Image.composite(soft, base, defocus_mask)

    bright = np.asarray(base, dtype=np.float32)
    luminance = bright.mean(axis=2)
    mask = np.clip((luminance - 170.0) / 85.0, 0.0, 1.0)[..., None]
    bloom = Image.fromarray(np.uint8(bright * mask), "RGB").filter(ImageFilter.GaussianBlur(9))
    result = Image.blend(base, Image.blend(base, bloom, 0.42), 0.12)
    if MONOCHROME:
        # Drop the colour last, so haze, bloom and vignette are all resolved
        # before the frame is flattened, and lift the contrast a little to
        # make up for the separation that colour was carrying.
        grey = np.asarray(result.convert("L"), dtype=np.float32) / 255.0
        grey = np.clip((grey - 0.5) * 1.12 + 0.5, 0.0, 1.0)
        result = Image.fromarray(np.uint8(grey * 255.0), "L").convert("RGB")
    return result


def resting_object_pose(robot, joints):
    _, tool0 = robot.link_poses(joints)
    attached = tool0 @ transform((0.0, 0.0, GRIPPER_OBJECT_OFFSET))
    return transform(attached[:3, 3])


def build_scene():
    scene = pyrender.Scene(
        bg_color=(0.13, 0.15, 0.16, 1.0),
        ambient_light=(
            0.185 * LIGHT_LEVEL,
            0.196 * LIGHT_LEVEL,
            0.198 * LIGHT_LEVEL,
        ),
    )
    rotating_nodes, conveyor_items, dynamic_nodes = add_environment(scene)
    add_lights(scene)

    actors: list[ArmActor] = []
    harnesses: list[HarnessActor] = []
    shared_objects: list[SharedObjectActor] = []
    harness_segment_mesh = cylinder_mesh(0.014, 1.0, MAT_HV_ORANGE, sections=28)

    def component_meshes(operation, side):
        """What each pair of hands is holding — the same parts the pallets
        carry, plus the tooling the two inspection stations work with."""
        hidden = box_mesh((0.001, 0.001, 0.001), MAT_BLACK)
        if operation == "connector_insert":
            return (
                hv_connector_mesh(),
                assembly_mesh(
                    [
                        (chamfer_box((0.032, 0.084, 0.084), 0.006), None, MAT_BLACK),
                        (
                            chamfer_box((0.018, 0.048, 0.048), 0.004),
                            transform((0.020, 0.0, 0.0)),
                            MAT_DARK_METAL,
                        ),
                    ]
                ),
            )
        if operation in ("main_route", "branch_route"):
            return (
                assembly_mesh(
                    [
                        (fillet_box((0.070, 0.058, 0.048), 0.008), None, MAT_HV_ORANGE),
                        (
                            chamfer_box((0.020, 0.036, 0.036), 0.004),
                            transform((0.042, 0.0, 0.0)),
                            MAT_DARK_METAL,
                        ),
                    ]
                ),
                assembly_mesh(
                    [
                        (chamfer_box((0.026, 0.068, 0.060), 0.005), None, MAT_BLACK),
                        (
                            chamfer_cylinder(0.014, 0.020, sections=16),
                            transform((0.018, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
                            MAT_DARK_METAL,
                        ),
                    ]
                ),
            )
        if operation == "clip_seat":
            return cable_clip_mesh(), hidden
        if operation == "latch_press":
            return toggle_latch_mesh(), hidden
        if operation == "electrical_test":
            probe_material = MAT_HV_ORANGE if side == "left" else MAT_BLACK
            # Spring-loaded test probe: body, collar, then the tip.
            return (
                assembly_mesh(
                    [
                        (
                            chamfer_box((0.038, 0.038, 0.140), 0.006),
                            None,
                            probe_material,
                        ),
                        (
                            chamfer_cylinder(0.016, 0.030, sections=20),
                            transform((0.0, 0.0, -0.082)),
                            MAT_BRUSHED,
                        ),
                        (
                            trimesh.creation.cylinder(radius=0.005, height=0.045, sections=12),
                            transform((0.0, 0.0, -0.112)),
                            MAT_STEEL,
                        ),
                        (
                            chamfer_cylinder(0.011, 0.024, sections=14),
                            transform((0.0, 0.0, 0.082)),
                            MAT_HOSE,
                        ),
                    ]
                ),
                sphere_mesh(0.025, MAT_BRUSHED),
            )
        if operation == "vision_inspect":
            # Hand-held inspection head with its lens and illuminator ring.
            return (
                assembly_mesh(
                    [
                        (
                            chamfer_box((0.120, 0.090, 0.080), 0.008),
                            None,
                            MAT_DARK_METAL,
                        ),
                        (
                            chamfer_cylinder(0.030, 0.034, sections=24),
                            transform((0.0, 0.0, -0.052)),
                            MAT_BRUSHED,
                        ),
                        (
                            trimesh.creation.annulus(r_min=0.032, r_max=0.046, height=0.012, sections=26),
                            transform((0.0, 0.0, -0.062)),
                            MAT_LAMP_OFF,
                        ),
                        (
                            chamfer_cylinder(0.011, 0.026, sections=14),
                            transform((0.066, 0.0, 0.020), rpy=(0.0, math.pi / 2.0, 0.0)),
                            MAT_HOSE,
                        ),
                    ]
                ),
                cylinder_mesh(0.028, 0.025, MAT_BLACK, sections=32),
            )
        return (
            assembly_mesh(
                [
                    (chamfer_box((0.070, 0.060, 0.025), 0.005), None, MAT_BLACK),
                    (
                        chamfer_box((0.044, 0.030, 0.012), 0.003),
                        transform((0.0, 0.0, 0.016)),
                        MAT_DARK_METAL,
                    ),
                ]
            ),
            hidden,
        )

    for cell_index, (cx, cy, initial_yaw) in enumerate(CELL_LAYOUT):
        operation = CELL_OPERATIONS[cell_index]
        center_pose = transform((cx, cy, 0.0))
        initial_root = center_pose @ rotate_z(initial_yaw)
        bases = (
            (("left", yoke_base_pose("left")),)
            if single_arm(cell_index)
            else (
                ("left", yoke_base_pose("left")),
                ("right", yoke_base_pose("right")),
            )
        )
        for side, base_local_pose in bases:
            robot = UR15(scene, initial_root @ base_local_pose)
            puck_mesh, collar_mesh = component_meshes(operation, side)
            puck_node = scene.add(puck_mesh, pose=np.eye(4))
            collar_node = scene.add(collar_mesh, pose=np.eye(4))
            stock_joints = L_STOCK if side == "left" else mirror_joint_pose(L_STOCK)
            place_joints = task_joint_pose(operation, side)
            pick_local_pose = np.linalg.inv(initial_root) @ resting_object_pose(robot, stock_joints)
            drop_local_pose = np.linalg.inv(initial_root) @ resting_object_pose(robot, place_joints)
            actors.append(
                ArmActor(
                    robot=robot,
                    puck_node=puck_node,
                    collar_node=collar_node,
                    cell_index=cell_index,
                    side=side,
                    operation=operation,
                    base_local_pose=base_local_pose,
                    pick_local_pose=pick_local_pose,
                    drop_local_pose=drop_local_pose,
                )
            )
        if operation in (
            "connector_insert",
            "main_route",
            "branch_route",
        ):
            harnesses.append(
                HarnessActor(
                    cell_index=cell_index,
                    operation=operation,
                    segment_nodes=[scene.add(harness_segment_mesh, pose=np.eye(4)) for _ in range(7)],
                )
            )
        # The part two hands carry together is the very part the pallet ends
        # up with, so it is the same mesh in both places.
        shared_specs = {
            "housing_load": (housing_assembly_mesh(), -0.195, 0.505),
            "strain_relief": (strain_relief_mesh(), -0.045, 0.675),
            "cover_place": (cover_assembly_mesh(), -0.126, 0.704),
        }
        if operation in shared_specs:
            mesh, center_z_offset, final_z = shared_specs[operation]
            shared_objects.append(
                SharedObjectActor(
                    cell_index=cell_index,
                    operation=operation,
                    node=scene.add(mesh, pose=np.eye(4)),
                    center_z_offset=center_z_offset,
                    final_z=final_z,
                )
            )

    palletiser = add_palletiser(scene)

    camera = pyrender.PerspectiveCamera(yfov=math.radians(40.0), znear=0.60, zfar=72.0)
    camera_node = scene.add(
        camera,
        pose=look_at((0.0, -11.4, 4.25), (0.0, 1.10, 1.08)),
    )
    scene.main_camera_node = camera_node
    return (
        scene,
        actors,
        harnesses,
        shared_objects,
        rotating_nodes,
        conveyor_items,
        dynamic_nodes,
        palletiser,
        camera_node,
    )


def cell_rotation_root(cell_index, seconds):
    cx, cy, initial_yaw = CELL_LAYOUT[cell_index]
    yaw = torso_yaw(
        seconds,
        initial_yaw,
        fetches_component(cell_index),
        cell_timing(cell_index),
    )
    return transform((cx, cy, 0.0)) @ rotate_z(yaw)


def cell_root(cell_index, seconds):
    cx, cy, initial_yaw = CELL_LAYOUT[cell_index]
    turns = fetches_component(cell_index)
    timing = cell_timing(cell_index)
    yaw = torso_yaw(seconds, initial_yaw, turns, timing)
    lift = lift_height(seconds, turns, timing)
    return transform((cx, cy, lift)) @ rotate_z(yaw)


def initial_cell_root(cell_index):
    cx, cy, initial_yaw = CELL_LAYOUT[cell_index]
    return transform((cx, cy, 0.0)) @ rotate_z(initial_yaw)


def conveyor_cell_root(cell_index):
    cx, cy, initial_yaw = CELL_LAYOUT[cell_index]
    return transform((cx, cy, 0.0)) @ rotate_z(initial_yaw + math.pi)


def conveyor_travel(seconds):
    """Advance every pallet by one station pitch per cycle."""
    return PANEL_PITCH * index_progress(seconds)


def completed_stage_at(y, phase):
    """How many stations have already worked on the pallet at this position."""
    station = (y - CELL_Y_START) / CELL_Y_SPACING
    stage = math.ceil(station - 1e-6)
    docked = int(round(station))
    # The pallet's own copy of the part appears when the hands let go of
    # theirs, not when it lands: any earlier and both copies are drawn in the
    # same place, which flickers.
    if abs(station - docked) < 1e-3 and 0 <= docked < len(CELL_LAYOUT) and phase >= STATION_PHASES[docked]["release"]:
        stage = docked + 1
    return int(min(max(stage, 0), len(CELL_LAYOUT)))


def update_actor(scene, actor, seconds, root):
    actor.robot.base_pose = root @ actor.base_local_pose
    joints, grip = motion_at(seconds, actor.side, actor.cell_index)
    tool0 = actor.robot.update(joints, grip)
    drops_component = actor.operation in (
        "connector_insert",
        "main_route",
        "branch_route",
        "clip_seat",
        "latch_press",
    )
    phase = cycle_phase(seconds)
    grasp = STOCK_GRASP + cell_timing(actor.cell_index)["shift"]
    carries_component = grasp <= phase < STATION_PHASES[actor.cell_index]["release"]
    if not drops_component or carries_component:
        puck_pose = tool0 @ transform((0.0, 0.0, GRIPPER_OBJECT_OFFSET))
    else:
        puck_pose = transform((0.0, 0.0, -10.0))
    scene.set_pose(actor.puck_node, pose=puck_pose)
    cell_x = CELL_LAYOUT[actor.cell_index][0]
    if actor.operation in (
        "connector_insert",
        "main_route",
        "branch_route",
    ):
        secondary_pose = puck_pose @ transform((math.copysign(0.058, cell_x), 0.0, 0.0))
    elif actor.operation == "electrical_test":
        secondary_pose = puck_pose @ transform((0.0, 0.0, -0.085))
    elif actor.operation == "vision_inspect":
        secondary_pose = puck_pose @ transform((0.0, 0.0, -0.052))
    else:
        secondary_pose = transform((0.0, 0.0, -10.0))
    scene.set_pose(actor.collar_node, pose=secondary_pose)
    return puck_pose


def cylinder_between_pose(start, end):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    direction = end - start
    length = float(np.linalg.norm(direction))
    if length < 1e-6:
        return transform(start)
    z_axis = direction / length
    reference = np.array((0.0, 0.0, 1.0)) if abs(z_axis[2]) < 0.9 else np.array((0.0, 1.0, 0.0))
    x_axis = np.cross(reference, z_axis)
    x_axis /= np.linalg.norm(x_axis)
    y_axis = np.cross(z_axis, x_axis)
    pose = np.eye(4)
    pose[:3, 0] = x_axis
    pose[:3, 1] = y_axis
    pose[:3, 2] = z_axis * length
    pose[:3, 3] = (start + end) * 0.5
    return pose


def update_harness(scene, harness, endpoint_poses):
    start = endpoint_poses["left"][:3, 3]
    end = endpoint_poses["right"][:3, 3]
    control = (start + end) * 0.5
    if harness.operation == "connector_insert":
        control[2] = max(0.54, min(start[2], end[2]) - 0.12)
    elif harness.operation == "main_route":
        control[2] = min(start[2], end[2]) - 0.035
    else:
        cell_x = CELL_LAYOUT[harness.cell_index][0]
        control[0] -= math.copysign(0.16, cell_x)
        control[2] = min(start[2], end[2]) - 0.025
    points = []
    for index in range(len(harness.segment_nodes) + 1):
        t = index / len(harness.segment_nodes)
        point = (1.0 - t) ** 2 * start + 2.0 * (1.0 - t) * t * control + t**2 * end
        points.append(point)
    for node, start_point, end_point in zip(
        harness.segment_nodes,
        points,
        points[1:],
    ):
        scene.set_pose(
            node,
            pose=cylinder_between_pose(start_point, end_point),
        )


def update_shared_object(scene, shared, endpoint_poses, seconds):
    """Carry a two-handed part on edge, clear of the cell column.

    Held flat between the grippers the part would sweep straight through the
    column while the table turns, so it is carried upright and in front of the
    body, then laid flat as it comes down onto the pallet.
    """
    phases = STATION_PHASES[shared.cell_index]
    timing = cell_timing(shared.cell_index)
    grasp = STOCK_GRASP + timing["shift"]
    phase = cycle_phase(seconds)
    if not grasp <= phase < phases["release"]:
        scene.set_pose(shared.node, pose=transform((0.0, 0.0, -10.0)))
        return
    left = endpoint_poses["left"][:3, 3]
    right = endpoint_poses["right"][:3, 3]
    centre = (left + right) * 0.5
    axis = right - left
    length = float(np.linalg.norm(axis))
    axis = axis / length if length > 1e-6 else np.array((1.0, 0.0, 0.0))
    settle = smootherstep((phase - phases["start"]) / max(phases["seat"] - phases["start"], 1e-6))
    # Hold the part out in front of the cell while it is being carried. The
    # direction has to turn with the table: held out along a fixed compass
    # bearing it swung through the column and the stereo head half way round
    # the turn, which is exactly where a part must never be.
    front = cell_rotation_root(shared.cell_index, seconds)[:3, :3] @ np.array((0.0, -1.0, 0.0))
    centre = centre + front * (1.0 - settle) * 0.16
    centre[2] += shared.center_z_offset * settle
    # The hands are posed by hand and stop a centimetre or two low, which puts
    # the part into the pallet instead of onto it. Ease the last of the drop
    # onto the height the pallet's own copy of this part will occupy — on the
    # clamped pallet, which is standing on its locating pins while this runs.
    target_z = shared.final_z + clamp_lift(seconds)
    centre[2] += (target_z - centre[2]) * settle
    # Carried on edge, which is how it stands in its magazine. It is laid
    # flat where it is set down, not on the way there: the arms hold it still
    # above their own station between the ready pose and the start of the
    # work, and that hold is the only part of the move it turns in. Spread
    # across the descent instead, the part tumbles for five seconds while it
    # travels, which is not how anything is carried.
    lay = smootherstep((phase - timing["ready"]) / max(phases["start"] - timing["ready"], 1e-6))
    pose = np.eye(4)
    pose[:3, :3] = Rotation.from_rotvec(axis * (1.0 - lay) * math.pi / 2.0).as_matrix()
    pose[:3, 3] = centre
    scene.set_pose(shared.node, pose=pose)


def camera_pose_at(seconds):
    """Fly one full orbit of the line, or hold the original wide view."""
    if INSPECT_VIEW is not None:
        return look_at(INSPECT_VIEW[0], INSPECT_VIEW[1])
    if CAMERA_MODE == "static":
        return look_at((6.80, 12.30, 5.40), (0.65, -0.50, 0.84))
    angle = ORBIT_START_ANGLE + 2.0 * math.pi * (max(0.0, seconds) / DURATION)
    # A gentle rise and fall twice per lap reads as a flown shot rather than a
    # turntable. Tying it to the angle keeps the loop exact.
    height = ORBIT_HEIGHT + ORBIT_HEIGHT_SWING * math.sin(2.0 * angle)
    return look_at(
        (
            ORBIT_CENTRE[0] + ORBIT_RADIUS * math.sin(angle),
            ORBIT_CENTRE[1] + ORBIT_RADIUS * math.cos(angle),
            height,
        ),
        (ORBIT_CENTRE[0], ORBIT_CENTRE[1], ORBIT_TARGET_Z),
    )


def dynamic_pose(kind, base_pose, seconds):
    """Drive station hardware straight from the transfer cycle."""
    if kind == "clamp":
        return transform((0.0, 0.0, clamp_lift(seconds))) @ base_pose
    if kind == "stopper":
        return transform((0.0, 0.0, stopper_extension(seconds))) @ base_pose
    phase = cycle_phase(seconds)
    working = INDEX_TIME <= phase < WORK_END
    lit = working if kind == "lamp_work" else not working
    return base_pose if lit else transform((0.0, 0.0, -10.0)) @ base_pose


def pose_scene(
    scene,
    actors,
    harnesses,
    shared_objects,
    rotating_nodes,
    conveyor_items,
    dynamic_nodes,
    palletiser,
    camera_node,
    seconds,
):
    """Put every moving thing where it belongs at this instant."""
    roots = [cell_root(cell_index, seconds) for cell_index in range(len(CELL_LAYOUT))]
    rotation_roots = [cell_rotation_root(cell_index, seconds) for cell_index in range(len(CELL_LAYOUT))]
    for rotating_node in rotating_nodes:
        root = roots[rotating_node.cell_index] if rotating_node.lifts else rotation_roots[rotating_node.cell_index]
        scene.set_pose(
            rotating_node.node,
            pose=root @ rotating_node.local_pose,
        )
    endpoint_poses: dict[int, dict[str, np.ndarray]] = {}
    for actor in actors:
        puck_pose = update_actor(
            scene,
            actor,
            seconds,
            roots[actor.cell_index],
        )
        endpoint_poses.setdefault(actor.cell_index, {})[actor.side] = puck_pose
    for harness in harnesses:
        update_harness(
            scene,
            harness,
            endpoint_poses[harness.cell_index],
        )
    for shared in shared_objects:
        update_shared_object(
            scene,
            shared,
            endpoint_poses[shared.cell_index],
            seconds,
        )

    update_palletiser(scene, palletiser, seconds)

    for mechanism in dynamic_nodes:
        scene.set_pose(
            mechanism.node,
            pose=dynamic_pose(mechanism.kind, mechanism.base_pose, seconds),
        )

    travel = conveyor_travel(seconds)
    lift = clamp_lift(seconds)
    phase = cycle_phase(seconds)
    for item in conveyor_items:
        y = CONVEYOR_Y_MIN + ((item.offset + travel) % CONVEYOR_LENGTH)
        hidden = item.required_stage > completed_stage_at(y, phase)
        # Only pallets held by a station stopper are raised onto their pins.
        docked = int(round((y - CELL_Y_START) / CELL_Y_SPACING))
        z = lift if 0 <= docked < len(CELL_LAYOUT) else 0.0
        scene.set_pose(
            item.node,
            pose=(transform((0.0, y, -10.0)) if hidden else transform((0.0, y, z)) @ item.local_pose),
        )

    scene.set_pose(camera_node, pose=camera_pose_at(seconds))


def render_frame(
    renderer,
    scene,
    actors,
    harnesses,
    shared_objects,
    rotating_nodes,
    conveyor_items,
    dynamic_nodes,
    palletiser,
    camera_node,
    seconds,
):
    pose_scene(
        scene,
        actors,
        harnesses,
        shared_objects,
        rotating_nodes,
        conveyor_items,
        dynamic_nodes,
        palletiser,
        camera_node,
        seconds,
    )
    shadow_flags = pyrender.RenderFlags.SHADOWS_SPOT
    color, depth = renderer.render(scene, flags=shadow_flags)
    # Keep the production view clean: no HUD, status bars, or angle indicators.
    return grade(Image.fromarray(color), depth)


def _triple(text):
    values = tuple(float(part) for part in text.split(","))
    if len(values) != 3:
        raise argparse.ArgumentTypeError("expected x,y,z")
    return values


def main():
    global CAMERA_MODE, MONOCHROME, INSPECT_VIEW
    parser = argparse.ArgumentParser()
    parser.add_argument("--still", type=Path)
    parser.add_argument("--time", type=float, default=4.8)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--duration", type=float, default=DURATION)
    parser.add_argument("--fps", type=int, default=FPS)
    parser.add_argument("--camera", choices=("orbit", "static"), default="orbit")
    parser.add_argument("--tone", choices=("mono", "colour"), default="mono")
    # Close inspection of a single part, for checking build detail.
    parser.add_argument("--eye", type=_triple)
    parser.add_argument("--target", type=_triple)
    args = parser.parse_args()
    CAMERA_MODE = args.camera
    MONOCHROME = args.tone == "mono"
    if args.eye is not None:
        if args.target is None:
            parser.error("--eye needs --target")
        INSPECT_VIEW = (args.eye, args.target)
    if not args.still and not args.video:
        parser.error("Use --still or --video")

    (
        scene,
        actors,
        harnesses,
        shared_objects,
        rotating_nodes,
        conveyor_items,
        dynamic_nodes,
        palletiser,
        camera_node,
    ) = build_scene()
    renderer = pyrender.OffscreenRenderer(WIDTH, HEIGHT)
    try:
        if args.still:
            frame = render_frame(
                renderer,
                scene,
                actors,
                harnesses,
                shared_objects,
                rotating_nodes,
                conveyor_items,
                dynamic_nodes,
                palletiser,
                camera_node,
                args.time,
            )
            args.still.parent.mkdir(parents=True, exist_ok=True)
            frame.save(args.still, quality=95)
            print(f"saved {args.still}")
        if args.video:
            args.video.parent.mkdir(parents=True, exist_ok=True)
            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "rawvideo",
                "-pixel_format",
                "rgb24",
                "-video_size",
                f"{WIDTH}x{HEIGHT}",
                "-framerate",
                str(args.fps),
                "-i",
                "-",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "slow",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(args.video),
            ]
            encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
            total = int(round(args.duration * args.fps))
            assert encoder.stdin is not None
            for index in range(total):
                seconds = args.start + index / args.fps
                frame = render_frame(
                    renderer,
                    scene,
                    actors,
                    harnesses,
                    shared_objects,
                    rotating_nodes,
                    conveyor_items,
                    dynamic_nodes,
                    palletiser,
                    camera_node,
                    seconds,
                )
                encoder.stdin.write(np.asarray(frame, dtype=np.uint8).tobytes())
                if index % args.fps == 0:
                    print(f"rendered {index}/{total}", flush=True)
            encoder.stdin.close()
            result = encoder.wait()
            if result != 0:
                raise RuntimeError(f"ffmpeg exited with {result}")
            print(f"saved {args.video}")
    finally:
        renderer.delete()


if __name__ == "__main__":
    main()
