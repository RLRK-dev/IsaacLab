# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build the existing box/cylinder outlines without scene-wide operators [m].

Same BMesh primitives, bevel settings and shading as allocation_product, using
data blocks so every screw does not force evaluation of the entire old scene.
"""

import bmesh
import bpy


def finish(name, data, mat, parent, location):
    mesh = bpy.data.meshes.new(name + "_mesh")
    data.to_mesh(mesh)
    data.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent, obj.location = parent, location
    return obj


def box(name, dimensions, location, mat, parent=None, bevel=0.0015):
    data = bmesh.new()
    bmesh.ops.create_cube(data, size=1)
    for vertex in data.verts:
        for axis in range(3):
            vertex.co[axis] *= dimensions[axis]
    obj = finish(name, data, mat, parent, location)
    if bevel:
        mod = obj.modifiers.new("Machined edge", "BEVEL")
        mod.width, mod.segments = min(bevel, min(dimensions) / 3), 3
    return obj


def cylinder(name, radius, depth, location, mat, parent=None, rotation=(0, 0, 0), vertices=48):
    data = bmesh.new()
    bmesh.ops.create_cone(
        data, cap_ends=True, cap_tris=False, segments=vertices, radius1=radius, radius2=radius, depth=depth
    )
    obj = finish(name, data, mat, parent, location)
    obj.rotation_euler = rotation
    mod = obj.modifiers.new("Edge radius", "BEVEL")
    mod.width, mod.segments = min(0.001, depth / 5), 2
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return obj
