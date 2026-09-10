# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Fixed OP030 split-station drivers and separated fastener presenters [m, rad].

Tool geometry reuses the v02 sockets, shaft and angle head. Mounts and feed-unit
envelopes are packaging candidates, not selected hardware or torque evidence.
The pure transform helpers can be imported outside Blender for IK planning.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    import bpy

FastenerKind = Literal["bolt", "nut"]
SIZES = {
    "M4": {
        "diameter": 0.004,
        "pitch": 0.0007,
        "flats": 0.007,
        "washer_d": 0.009,
        "washer_h": 0.0008,
        "head_h": 0.0028,
        "nut_h": 0.0032,
        "bolt_length": 0.016,
    },
    "M6": {
        "diameter": 0.006,
        "pitch": 0.0010,
        "flats": 0.010,
        "washer_d": 0.012,
        "washer_h": 0.0016,
        "head_h": 0.0040,
        "nut_h": 0.0050,
        "bolt_length": 0.016,
    },
    "M14": {
        "diameter": 0.014,
        "pitch": 0.0020,
        "flats": 0.022,
        "washer_d": 0.028,
        "washer_h": 0.0025,
        "head_h": 0.0090,
        "nut_h": 0.0110,
        "bolt_length": 0.025,
    },
}


def driver_flange_to_tcp(size: str) -> np.ndarray:
    """Return the fixed tool0-to-socket-mouth transform [m].

    Socket local +Z points from the workpiece into the tool. Thus insertion is
    along socket -Z. The input flange is original UR15 FK ``tool0``; it is not
    the shifted wrist visual origin or a previous finger contact point.
    """
    if size not in SIZES:
        raise ValueError(size)
    result = np.eye(4)
    if size == "M6":
        result[:3, :3] = ((0, 1, 0), (0, 0, -1), (-1, 0, 0))
        result[:3, 3] = (0, 0.153, 0.318)
    else:
        result[:3, :3] = np.diag((1, -1, -1))
        result[2, 3] = 0.300
    return result


def flange_target_for_tcp(tcp_world: np.ndarray, size: str) -> np.ndarray:
    """Convert a desired socket-mouth world pose [m] to original FK tool0."""
    return np.asarray(tcp_world, dtype=float) @ np.linalg.inv(driver_flange_to_tcp(size))


def fastener_socket_offset(size: str, kind: FastenerKind) -> float:
    """Return socket-mouth offset above the fastener washer seat [m]."""
    _validate_kind(kind)
    return float(SIZES[size]["washer_h"] + 0.0003)


def feeder_queue_poses(size: str, count: int, consumed: int = 0, advance: float = 0.0) -> list[np.ndarray | None]:
    """Return finite single-file fastener poses in presenter coordinates [m].

    Args:
        size: Nominal thread size.
        count: Number of individually tracked fasteners initially supplied.
        consumed: Fasteners already removed from the presenter.
        advance: Next escapement transfer fraction in [0, 1]. At 1 the next
            fastener reaches the pick nest; consumed actors return None.
    """
    if not 0 <= consumed <= count or not 0 <= advance <= 1:
        raise ValueError("Invalid finite presenter state")
    pitch = max(0.025, SIZES[size]["washer_d"] + 0.014)
    result = []
    for index in range(count):
        if index < consumed:
            result.append(None)
            continue
        matrix = np.eye(4)
        matrix[0, 3] = -(index - consumed + (1 - advance)) * pitch
        result.append(matrix)
    return result


def _validate_kind(kind: str) -> None:
    if kind not in ("bolt", "nut"):
        raise ValueError(kind)


@dataclass
class DriverAssembly:
    """Blender objects and calibrated fixed mount transform [m]."""

    root: bpy.types.Object
    tool: bpy.types.Object
    spindle: bpy.types.Object
    flange_to_tcp: np.ndarray
    camera_record: dict
    removed_gripper_meshes: list[str]


@dataclass
class FeederAssembly:
    """Finite presenter actors and pickup frame [m]."""

    root: bpy.types.Object
    escapement: bpy.types.Object
    pickup: bpy.types.Object
    fasteners: list[bpy.types.Object]
    size: str
    kind: FastenerKind


def _blender():
    import bpy
    from allocation_product import empty
    from mathutils import Matrix, Vector
    from op020_jb_geometry import box, cylinder, materials
    from op030_geometry import nut, nutrunner, ring, thread_stud

    return bpy, Matrix, Vector, empty, box, cylinder, materials, nut, nutrunner, ring, thread_stud


def _beam(name, start, end, width, depth, material, parent):
    _, _, Vector, _, box, *_ = _blender()
    start, end = Vector(start), Vector(end)
    obj = box(name, (width, depth, (end - start).length), (start + end) / 2, material, parent, 0.0006)
    obj.rotation_euler = (end - start).to_track_quat("Z", "Y").to_euler()
    return obj


def remove_gripper_meshes(
    nodes: list[bpy.types.Object], *, preserve: list[bpy.types.Object] | None = None
) -> list[str]:
    """Remove only specified gripper mesh descendants, retaining FK empties.

    Camera assemblies should be transferred to their new flange first. The
    explicit preserve list also protects all descendants from deletion.
    """
    bpy, *_ = _blender()
    protected = set()
    for root in preserve or []:
        protected.update((root, *root.children_recursive))
    removed = []
    candidates = {obj for node in nodes for obj in (node, *node.children_recursive)}
    for obj in sorted(candidates, key=lambda item: item.name):
        if obj.type == "MESH" and obj not in protected:
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def _camera_mount(camera_root, flange, size, side, parent, optical_center=None):
    """Re-aim the same camera geometry and bridge its mounting tab [m]."""
    bpy, Matrix, Vector, _, box, _, materials, *_ = _blender()
    cameras = [obj for obj in camera_root.children_recursive if obj.type == "CAMERA"]
    if len(cameras) != 1:
        raise ValueError("Exactly one original on-hand camera is required")
    camera = cameras[0]
    meshes = [obj for obj in camera_root.children_recursive if obj.type == "MESH"]
    old_world = camera.matrix_world.copy()
    old_optical = camera_root.matrix_world.inverted() @ camera.matrix_world
    side_sign = -1 if side == "left" else 1
    tcp = driver_flange_to_tcp(size)[:3, 3]
    position = Vector((side_sign * 0.09, 0, 0.190))
    if size == "M6":
        position = Vector((side_sign * 0.090, 0.095, 0.280))
    if optical_center is not None:
        position = Vector(optical_center)
    desired = (Vector(tcp) - position).to_track_quat("-Z", "Y").to_matrix().to_4x4()
    desired.translation = position
    camera_root.parent = flange
    camera_root.matrix_parent_inverse = Matrix.Identity(4)
    camera_root.animation_data_clear()
    camera_root.matrix_basis = desired @ old_optical.inverted()
    bpy.context.view_layer.update()
    tabs = [obj for obj in meshes if "mount_tab" in obj.name]
    if len(tabs) != 1:
        raise ValueError("Original camera mount tab is missing")
    tab = tabs[0]
    local_center = sum((vertex.co for vertex in tab.data.vertices), Vector()) / len(tab.data.vertices)
    tab_at_flange = flange.matrix_world.inverted() @ tab.matrix_world @ local_center
    start = Vector((side_sign * 0.035, 0, 0.012))
    midway = Vector((side_sign * 0.075, 0, 0.060))
    _beam(parent.name + "_camera_bridge_base", start, midway, 0.014, 0.006, materials()["metal"], parent)
    _beam(parent.name + "_camera_bridge_arm", midway, tab_at_flange, 0.014, 0.006, materials()["metal"], parent)
    # The original tab remains intact. The bridge terminates on its broad
    # mounting surface; the solid overlap is an intentional bolted interface.
    box(parent.name + "_camera_bridge_pad", (0.010, 0.018, 0.010), tab_at_flange, materials()["metal"], parent, 0.001)
    camera_root["mount_frame"] = "rigid wrist tool0; original camera meshes and intrinsics, new TCP aim"
    return {
        "camera": camera.name,
        "retained_meshes": [obj.name for obj in meshes],
        "mesh_data_names": [obj.data.name for obj in meshes],
        "previous_world": [list(row) for row in old_world],
        "new_flange_to_camera": [list(row) for row in desired],
        "new_flange_to_camera_group": [list(row) for row in camera_root.matrix_basis],
        "mount_tab_center_flange_m": list(tab_at_flange),
        "intrinsics": {
            "lens_mm": camera.data.lens,
            "sensor_width_mm": camera.data.sensor_width,
            "sensor_fit": camera.data.sensor_fit,
        },
        "scope": "same optics geometry/intrinsics; provisional rigid bracket; no visibility or stiffness approval",
    }


def build_fixed_driver(
    name: str,
    size: str,
    flange: bpy.types.Object,
    *,
    fastener_kind: FastenerKind,
    gripper_nodes: list[bpy.types.Object] | None = None,
    camera_root: bpy.types.Object | None = None,
    side: Literal["left", "right"] = "left",
    camera_position: tuple[float, float, float] | None = None,
) -> DriverAssembly:
    """Build a driver rigidly mounted to original FK tool0 [m].

    Args:
        name: Unique new assembly name.
        size: M4, M6 or M14; reuse corresponding v02 spindle geometry.
        flange: Empty animated at the original UR15 FK tool0 world transform.
        fastener_kind: Explicit bolt/nut interface; never inferred from size.
        gripper_nodes: Exact source gripper roots whose meshes are removed.
        camera_root: Existing on-hand camera assembly to retain and support.
        side: Original side, used for the external camera bracket direction.
        camera_position: Optional optical center in the flange frame [m],
            retaining the original meshes and aiming at the socket TCP.
    """
    _validate_kind(fastener_kind)
    bpy, Matrix, _, empty, box, cylinder, materials, _, nutrunner, ring, _ = _blender()
    if bpy.data.objects.get(name):
        raise ValueError(f"Assembly already exists: {name}")
    mats = materials()
    root = empty(name, flange)
    root.matrix_parent_inverse = Matrix.Identity(4)
    tool, spindle = nutrunner(name + "_tool", size)
    for obj in list(tool.children_recursive):
        if any(token in obj.name for token in ("_battery", "_handle", "_grip_flat")):
            bpy.data.objects.remove(obj, do_unlink=True)
    tool.parent = root
    tool.matrix_parent_inverse = Matrix.Identity(4)
    transform = driver_flange_to_tcp(size)
    tool.matrix_basis = Matrix(transform.tolist())
    for key in ("grip_contact_local_m", "grip_width_m"):
        if key in tool:
            del tool[key]
    tool["scope"] = "fixed robot spindle envelope; reused socket/shaft/angle head; selected hardware not defined"
    tool["fastener_kind"] = fastener_kind
    # The wrist surface ends at tool0 Z≈0. This plate begins at Z=0 and
    # connects to the rear end of the stationary motor through a short sleeve.
    adapter = ring(name + "_wrist_adapter", 0.007, 0.0375, 0.012, (0, 0, 0.006), mats["metal"], root)
    cylinder(
        name + "_motor_coupler",
        0.018,
        0.026 if size == "M6" else 0.010,
        (0, 0, 0.025 if size == "M6" else 0.017),
        mats["black"],
        root,
    )
    for index in range(4):
        angle = math.pi / 4 + index * math.pi / 2
        xy = (0.025 * math.cos(angle), 0.025 * math.sin(angle))
        cutter = cylinder(name + f"_clearance_cutter_{index}", 0.0032, 0.020, (*xy, 0.006), mats["metal"], root)
        bpy.context.view_layer.update()
        modifier = adapter.modifiers.new(name="mounting_clearance", type="BOOLEAN")
        modifier.operation, modifier.solver, modifier.object = "DIFFERENCE", "EXACT", cutter
        with bpy.context.temp_override(object=adapter, active_object=adapter):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
        cylinder(name + f"_adapter_bolt_{index}_shank", 0.003, 0.018, (*xy, 0.003), mats["metal"], root)
        cylinder(name + f"_adapter_bolt_{index}_head_base", 0.005, 0.003, (*xy, 0.0135), mats["metal"], root)
        ring(
            name + f"_adapter_bolt_{index}_head_socket",
            0.0025,
            0.005,
            0.003,
            (*xy, 0.0165),
            mats["metal"],
            root,
            hex_inner=True,
        )
    service_x = 0.0335 if side == "left" else -0.0335
    box(name + "_drive_service_box", (0.025, 0.030, 0.050), (service_x, 0, 0.070), mats["black"], root, 0.002)
    cylinder(name + "_local_service_gland", 0.006, 0.012, (service_x, 0, 0.040), mats["metal"], root)
    ring(
        name + "_vacuum_retention_tip",
        SIZES[size]["flats"] / 2 + 0.00016,
        {"M4": 0.006, "M6": 0.008, "M14": 0.016}[size],
        0.002,
        (0, 0, 0.001),
        mats["black"],
        spindle,
        hex_inner=True,
    )
    camera_record = _camera_mount(camera_root, flange, size, side, root, camera_position) if camera_root else {}
    removed = remove_gripper_meshes(gripper_nodes or [], preserve=[root, *([camera_root] if camera_root else [])])
    root["mount"] = "permanently parented to original UR15 tool0; no gripper-held tool and no tool pickup"
    root["nominal_adapter_pattern"] = "UR15 ISO 9409-1-50-4-M6; 50 mm PCD; four M6; custom plate remains provisional"
    root["adapter_bolt_engagement_m"] = 0.006
    root["flange_to_tcp"] = transform.ravel().tolist()
    root["fastener_kind"], root["thread_size"] = fastener_kind, size
    root["stroke_scope"] = "robot axial approach; spindle turn is kinematic, no torque/contact result"
    return DriverAssembly(root, tool, spindle, transform, camera_record, removed)


def build_fastener(
    name: str, size: str, kind: FastenerKind, parent: bpy.types.Object | None = None
) -> bpy.types.Object:
    """Create an individually tracked bolt or nut/washer set [m].

    The local origin is the washer seat. Bolt shanks extend in local -Z;
    nut bores are open in +Z. New M6/M14 bolts are optional candidates only.
    """
    _validate_kind(kind)
    _, _, _, empty, _, cylinder, materials, nut, _, ring, thread_stud = _blender()
    if kind == "nut":
        root = nut(name, size, parent)
    else:
        spec = SIZES[size]
        root = empty(name, parent)
        metal = materials()["metal"]
        ring(
            name + "_washer",
            spec["diameter"] / 2 + 0.0002,
            spec["washer_d"] / 2,
            spec["washer_h"],
            (0, 0, spec["washer_h"] / 2),
            metal,
            root,
        )
        head = cylinder(
            name + "_hex_head",
            spec["flats"] / math.sqrt(3),
            spec["head_h"],
            (0, 0, spec["washer_h"] + spec["head_h"] / 2),
            metal,
            root,
            vertices=6,
        )
        head.rotation_euler.z = math.pi / 6
        shaft = thread_stud(name + "_thread", spec["diameter"], spec["pitch"], spec["bolt_length"], metal, root)
        shaft.location.z = spec["washer_h"] - spec["bolt_length"]
        root["under_head_length_m"] = spec["bolt_length"]
        root["shank_end_local_m"] = spec["washer_h"] - spec["bolt_length"]
    root["fastener_uid"], root["fastener_kind"], root["thread_size"] = name, kind, size
    root["supply_scope"] = "individually tracked fastener with retained washer; captive-washer product unselected"
    return root


def convert_support_mounts_to_bolts(
    product: bpy.types.Object,
    *,
    plate: bpy.types.Object | None = None,
    receivers: bpy.types.Object | None = None,
) -> dict:
    """Replace four M4 studs with flanged threaded-insert envelopes [m].

    Original support ears still seat at product Z=0.007 and their bolt washer
    seats stay at Z=0.013. Four local outer bores accept the insert shanks;
    the retained plate geometry outside these bores is not redesigned.

    Args:
        product: Same JB assembly continued from OP020.
        plate: Actual B03 mesh; inferred from the retained p03 name if omitted.
        receivers: Existing preinstalled-mount-studs root, including its four
            receiver empties. Its name may have a station prefix.

    Returns:
        Names, sizes, removed studs and the explicit provisional scope.
    """
    bpy, _, _, _, _, cylinder, materials, _, _, ring, _ = _blender()
    if plate is None:
        candidates = [
            obj
            for obj in product.children_recursive
            if obj.type == "MESH" and "_B01_B02_B03" in obj.name and obj.name.endswith("_p03")
        ]
        if len(candidates) != 1:
            raise ValueError("Provide the exact retained B03 p03 mesh")
        plate = candidates[0]
    if receivers is None:
        candidates = [obj for obj in product.children_recursive if "B03_preinstalled_mount_studs" in obj.name]
        if len(candidates) != 1:
            raise ValueError("Provide the exact four-receiver root")
        receivers = candidates[0]
    if receivers.get("split_bolt_conversion"):
        raise ValueError("M4 support interface was already converted")
    receiver_roots = [obj for obj in receivers.children if obj.type == "EMPTY"]
    if len(receiver_roots) != 4:
        raise ValueError("Expected exactly four support receivers")
    removed, centers = [], []
    metal = materials()["metal"]
    # Avoid modifying the shared source datablock used by other products.
    plate.data = plate.data.copy()
    import bmesh

    mesh = bmesh.new()
    mesh.from_mesh(plate.data)
    bmesh.ops.remove_doubles(mesh, verts=list(mesh.verts), dist=1e-7)
    bmesh.ops.recalc_face_normals(mesh, faces=list(mesh.faces))
    bpy.context.view_layer.update()
    # The inherited object combines seven overlapping but independently closed
    # solids. Boolean only the broad upper mounting plate, preserving the
    # lower plate and the five ribs exactly instead of unioning those solids.
    remaining = set(mesh.verts)
    components = []
    local_to_product = product.matrix_world.inverted() @ plate.matrix_world
    while remaining:
        vertices = {remaining.pop()}
        todo = list(vertices)
        while todo:
            vertex = todo.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other)
                    vertices.add(other)
                    todo.append(other)
        points = np.asarray([local_to_product @ vertex.co for vertex in vertices])
        components.append((vertices, points.min(0), points.max(0)))
    selected = [
        vertices
        for vertices, low, high in components
        if abs(high[2] - 0.004) < 1e-6 and low[0] < -0.17 and high[0] > 0.17 and low[1] < -0.20 and high[1] > 0.20
    ]
    if len(selected) != 1:
        mesh.free()
        raise ValueError("Cannot uniquely identify the retained B03 upper support plate")
    selected = selected[0]
    selected_faces = {face for vertex in selected for face in vertex.link_faces}
    isolated_vertices = list(selected)
    indices = {vertex: index for index, vertex in enumerate(isolated_vertices)}
    data = bpy.data.meshes.new(plate.name + "_isolated_support")
    data.from_pydata(
        [vertex.co[:] for vertex in isolated_vertices],
        [],
        [[indices[vertex] for vertex in face.verts] for face in selected_faces],
    )
    bore_surface = bpy.data.objects.new(plate.name + "_bore_working", data)
    bpy.context.scene.collection.objects.link(bore_surface)
    bore_surface.matrix_world = plate.matrix_world.copy()
    for receiver in receiver_roots:
        center = product.matrix_world.inverted() @ receiver.matrix_world.translation
        centers.append([float(center.x), float(center.y)])
        for child in list(receiver.children):
            if child.type == "MESH" and child.name.endswith(("_M4", "_weld_base")):
                removed.append(child.name)
                bpy.data.objects.remove(child, do_unlink=True)
        cutter = cylinder(
            receiver.name + "_insert_bore_cutter",
            0.0056,
            0.080,
            (float(center.x), float(center.y), 0.0),
            metal,
            product,
            vertices=64,
        )
        bpy.context.view_layer.update()
        modifier = bore_surface.modifiers.new(name="support_insert_clearance", type="BOOLEAN")
        modifier.operation, modifier.solver, modifier.object = "DIFFERENCE", "EXACT", cutter
        with bpy.context.temp_override(object=bore_surface, active_object=bore_surface):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
        ring(receiver.name + "_threaded_insert_shank", 0.0021, 0.0055, 0.009, (0, 0, -0.0045), metal, receiver)
        ring(receiver.name + "_threaded_insert_flange", 0.0021, 0.007, 0.003, (0, 0, 0.0015), metal, receiver)
        receiver["interface"] = "M4 bolt into flanged threaded insert; female bore is clearance-envelope geometry"
    untouched = [vertex for vertex in mesh.verts if vertex not in selected]
    indices = {vertex: index for index, vertex in enumerate(untouched)}
    new_vertices = [vertex.co[:] for vertex in untouched]
    new_faces = [[indices[vertex] for vertex in face.verts] for face in mesh.faces if face not in selected_faces]
    offset = len(new_vertices)
    new_vertices.extend(vertex.co[:] for vertex in bore_surface.data.vertices)
    new_faces.extend([[index + offset for index in face.vertices] for face in bore_surface.data.polygons])
    output = bpy.data.meshes.new(plate.data.name + "_four_local_bores")
    output.from_pydata(new_vertices, [], new_faces)
    for material in plate.data.materials:
        output.materials.append(material)
    plate.data = output
    bpy.data.objects.remove(bore_surface, do_unlink=True)
    mesh.free()
    receivers["split_bolt_conversion"] = True
    receivers["process_scope"] = "B03 supplied with four flanged M4 inserts; ST A supplies M4x16 bolts automatically"
    record = {
        "plate": plate.name,
        "receiver_roots": [obj.name for obj in receiver_roots],
        "removed_meshes": removed,
        "centers_product_xy_m": centers,
        "plate_insert_bore_diameter_m": 0.0112,
        "insert_shank_diameter_m": 0.011,
        "insert_flange_diameter_m": 0.014,
        "insert_thread_envelope_diameter_m": 0.0042,
        "insert_bottom_product_z_m": -0.005,
        "insert_top_product_z_m": 0.007,
        "support_ear_seat_product_z_m": 0.007,
        "bolt_washer_seat_product_z_m": 0.013,
        "bolt_under_head_length_m": 0.016,
        "bolt_tip_product_z_m": -0.0022,
        "bolt_tip_to_insert_bottom_m": 0.0028,
        "scope": "provisional M4 threaded-insert geometry; retention, thread contact, material and torque unselected",
    }
    return record


def _copy_fastener(template, name, parent):
    bpy, Matrix, _, empty, *_ = _blender()
    root = empty(name, parent)
    for key, value in template.items():
        root[key] = value
    root["fastener_uid"] = name
    for child in template.children:
        copied = child.copy()
        copied.name = name + child.name.removeprefix(template.name)
        bpy.context.scene.collection.objects.link(copied)
        copied.parent = root
        copied.matrix_parent_inverse = Matrix.Identity(4)
        copied.matrix_basis = child.matrix_basis.copy()
    return root


def build_fastener_feeder(
    name: str,
    size: str,
    kind: FastenerKind,
    pose: np.ndarray,
    *,
    count: int = 12,
    min_rail_length: float = 0.34,
) -> FeederAssembly:
    """Build a covered automatic presenter with a separated pick nest [m].

    The root is the pick-nest washer seat with fastener axis +Z. Bolts/nuts
    emerge single-file from a covered hopper, are separated by an escapement,
    then picked by the permanently mounted vacuum/socket tool. There is no
    loose flat tray and no moving feed hose across the robot workspace.

    Args:
        name: Root actor name and UID prefix.
        size: Nominal M4, M6 or M14.
        kind: Bolt or nut geometry.
        pose: Pick-nest world frame [m].
        count: Finite number of tracked fasteners.
        min_rail_length: Minimum nose-to-upstream rail span [m]. Increasing
            this moves the hopper and drive upstream and extends the support
            base while preserving the pick nest, queue pitch and all UIDs.
    """
    _validate_kind(kind)
    if not 1 <= count <= 40:
        raise ValueError("Feeder model count must be 1..40")
    if not math.isfinite(min_rail_length) or min_rail_length < 0.34:
        raise ValueError("Minimum rail length must be finite and at least 0.34 m")
    bpy, Matrix, _, empty, box, cylinder, materials, _, _, ring, _ = _blender()
    if bpy.data.objects.get(name):
        raise ValueError(f"Feeder already exists: {name}")
    spec, mats = SIZES[size], materials()
    root = empty(name)
    root.matrix_world = Matrix(np.asarray(pose).tolist())
    pitch = max(0.025, spec["washer_d"] + 0.014)
    rail_length = max(min_rail_length, (count - 1) * pitch + 0.04)
    box(name + "_base", (rail_length + 0.10, 0.23, 0.014), (-rail_length / 2, 0, -0.165), mats["metal"], root)
    box(name + "_drive_enclosure", (0.23, 0.20, 0.13), (-rail_length + 0.10, 0, -0.092), mats["white"], root)
    # Covered bulk reservoir; the internal orienting path is a conceptual
    # envelope, while all visible queue and escapement actors are explicit.
    box(name + "_hopper_body", (0.22, 0.19, 0.16), (-rail_length + 0.10, 0, 0.065), mats["white"], root)
    box(name + "_hopper_lid", (0.23, 0.20, 0.009), (-rail_length + 0.10, 0, 0.1495), mats["metal"], root)
    box(name + "_hopper_handle", (0.055, 0.015, 0.016), (-rail_length + 0.10, 0, 0.162), mats["black"], root)
    slot = spec["diameter"] / 2 + 0.0003
    for sign in (-1, 1):
        box(
            name + f"_feed_rail_{sign}",
            (rail_length, 0.006, 0.010),
            (-rail_length / 2, sign * (slot + 0.003), -0.005),
            mats["metal"],
            root,
            0.0001,
        )
        box(
            name + f"_outer_guide_{sign}",
            (rail_length - 0.025, 0.004, 0.018),
            (-(rail_length + 0.025) / 2, sign * (spec["washer_d"] / 2 + 0.003), 0.001),
            mats["blue"],
            root,
            0.0002,
        )
    # A clearance-bored seat supports the washer and leaves the bolt shank
    # below it free. Its top is exactly the actor-origin washer seat z=0.
    ring(name + "_pick_nest", slot, spec["washer_d"] / 2 + 0.004, 0.012, (0, 0, -0.006), mats["blue"], root)
    ring(name + "_nose_support", slot, 0.036, 0.050, (0, 0, -0.045), mats["metal"], root)
    box(name + "_nose_pedestal", (0.045, 0.075, 0.077), (0.006, 0, -0.1085), mats["white"], root)
    cylinder(
        name + "_present_sensor",
        0.006,
        0.020,
        (0.035, 0.025, -0.008),
        mats["black"],
        root,
        rotation=(0, math.pi / 2, 0),
    )
    escapement = empty(name + "_escapement", root)
    box(
        name + "_escapement_gate",
        (0.006, spec["washer_d"] + 0.010, 0.010),
        (-pitch * 0.6, 0, 0.006),
        mats["black"],
        escapement,
    )
    box(name + "_gate_slide", (0.018, 0.022, 0.050), (-pitch * 0.6, 0.048, -0.013), mats["metal"], escapement)
    box(name + "_gate_actuator", (0.045, 0.055, 0.070), (-pitch * 0.6, 0.068, -0.030), mats["white"], root)
    pickup = empty(name + "_pickup_socket_tcp", root)
    pickup.location.z = fastener_socket_offset(size, kind)
    fasteners = [build_fastener(name + "_UID001", size, kind, root)]
    for index in range(1, count):
        fasteners.append(_copy_fastener(fasteners[0], name + f"_UID{index + 1:03d}", root))
    for obj, matrix in zip(fasteners, feeder_queue_poses(size, count, advance=1), strict=True):
        obj.matrix_basis = Matrix(matrix.tolist())
    root["thread_size"], root["fastener_kind"], root["tracked_fastener_count"] = size, kind, count
    root["rail_length_m"], root["minimum_rail_length_m"] = rail_length, min_rail_length
    root["supply_architecture"] = (
        "covered orienting hopper; single-file guide; powered escapement; vacuum/socket pickup"
    )
    root["scope"] = "provisional feed-unit packaging and finite actor transfer; bulk sorting physics/PLC not simulated"
    return FeederAssembly(root, escapement, pickup, fasteners, size, kind)
