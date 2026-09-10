# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Native rigid and exact sampled cable animation helpers for split OP030 [m]."""

import bpy
import numpy as np
from build_jb_op020 import animate_channels
from continuous_common import action_world
from mathutils import Matrix


def bake_world(obj, matrices, frames):
    """Bake absolute poses [m] without interpreting them as parent-local poses."""
    obj.parent = None
    obj.matrix_parent_inverse = Matrix.Identity(4)
    action_world(obj, np.asarray(matrices), np.asarray(frames))


def bake_local(obj, matrices, frames):
    """Bake parent-relative rigid transforms [m] while retaining the parent."""
    obj.matrix_parent_inverse = Matrix.Identity(4)
    action_world(obj, np.asarray(matrices), np.asarray(frames))


def bake_wire(uid, frames, root_poses, parameters, lug_world, shape_parameters, shape_vertices):
    """Bake one persistent wire using exact native-frame deformation keys [m].

    Rigid transport reuses a deformation key. Only distinct straight/bend or
    terminal-raise values create keys; every rendered native sample points to
    its own exact shape, avoiding an approximate sparse deformation basis.
    """
    root = bpy.data.objects[uid]
    insulation = bpy.data.objects[uid + "_insulation"]
    frames = np.asarray(frames)
    parameters = np.asarray(parameters)
    unique, inverse = np.unique(parameters, return_inverse=True)
    if np.any(unique < -1e-8) or np.any(unique > 2.0 + 1e-8):
        raise ValueError("Wire deformation outside its defined straight/bend/insertion states")
    if not np.array_equal(unique, shape_parameters):
        raise ValueError("Prepared mesh samples differ from the exact native deformation parameters")
    vertices = shape_vertices[0]
    if len(insulation.data.vertices) != len(vertices):
        raise ValueError("Wire tube topology changed")
    if insulation.data.shape_keys:
        insulation.shape_key_clear()
    insulation.data.vertices.foreach_set("co", vertices.ravel())
    insulation.data.update()
    # Absolute key times are integers, so their exact values survive native
    # float conversion. A native frame always lands on one complete key.
    for index, parameter in enumerate(unique):
        key = insulation.shape_key_add(name=f"deformation_{index:05d}")
        key.interpolation = "KEY_LINEAR"
        points = shape_vertices[index]
        if points.shape != vertices.shape or not np.isfinite(points).all():
            raise ValueError("A deformation changed tube topology")
        key.data.foreach_set("co", points.ravel())
    insulation.data.shape_keys.use_relative = False
    with bpy.context.temp_override(object=insulation, active_object=insulation):
        bpy.ops.object.shape_key_retime()
    key_times = np.array([key.frame for key in insulation.data.shape_keys.key_blocks])
    if len(key_times) > 1 and not np.all(np.diff(key_times) > 0):
        raise RuntimeError("Absolute deformation key times must increase")
    animate_channels(insulation.data.shape_keys, "eval_time", key_times[inverse], frames)
    root_poses = np.asarray(root_poses)
    bake_world(root, root_poses, frames)
    inverse_root = np.linalg.inv(root_poses)
    for end in ("J1", "T"):
        lug = bpy.data.objects[uid + "_" + end]
        lug.parent = root
        local = inverse_root @ np.asarray(lug_world[end])
        bake_local(lug, local, frames)
    insulation["deformation_scope"] = (
        "Exact native-frame shape samples; no material force or manufacturing tolerance model"
    )
    insulation["deformation_key_count"] = len(unique)
    return dict(
        uid=uid,
        samples=len(frames),
        deformation_keys=len(unique),
        vertices=len(vertices),
        parameter_min=float(unique[0]),
        parameter_max=float(unique[-1]),
    )
