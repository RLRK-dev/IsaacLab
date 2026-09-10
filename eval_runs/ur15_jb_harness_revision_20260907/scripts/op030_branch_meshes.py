# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Use the established FCL library on retained native triangles [m]."""

import sys

import numpy as np

try:
    import fcl
except ImportError:
    sys.path.insert(0, "/tmp/ur15_op030_fcl")
    import fcl

from op030_definition import ROOT


class BranchMeshes:
    def __init__(self):
        with np.load(ROOT / "data/op030_branch_meshes.npz") as saved:
            d = {k: saved[k].copy() for k in saved.files}
        self.nodes, self.names, self.actors = d["nodes"], d["names"], d["actors"]
        self.fixed_base = d["fixed_base"]
        self.actor_indices = {name: np.flatnonzero(self.actors == name) for name in set(self.actors)}
        self.side = np.where(self.nodes < 0, -2, np.where(self.nodes < 1000, -1, np.where(self.nodes < 1084, 0, 1)))
        local_node = self.nodes - np.where(self.side == 0, 1046, 1086)
        links = np.searchsorted([3, 5, 10, 15, 18, 20, 21, 38], local_node, side="right")
        a, b = np.triu_indices(len(self.nodes), 1)
        relevant = (self.side[a] >= 0) | (self.side[b] >= 0)
        nonadjacent = (
            (self.side[a] < 0) | (self.side[b] < 0) | (self.side[a] != self.side[b]) | (abs(links[a] - links[b]) > 1)
        )
        mount = ((self.nodes[a] == 578) & np.isin(self.nodes[b], [1046, 1086])) | (
            (self.nodes[b] == 578) & np.isin(self.nodes[a], [1046, 1086])
        )
        use = nonadjacent & ~mount

        # Branch preference omits only these authored gripping interfaces;
        # the native contact audit must still check their relative geometry.
        def grip_interface(first, second):
            precision = first.startswith("OP030_precision_") and first.endswith(("_tip", "_stem"))
            tool_flat = second.startswith("OP030_driver_") and "_grip_flat" in second
            terminal_disc = second.startswith(("OP030_T01_UID001", "OP030_T02_UID001")) and second.endswith(
                "_insulator"
            )
            sleeve = (
                first.startswith("OP030_precision_right_")
                and second.startswith("OP030_H03_")
                and second.endswith("_J1_heatshrink")
            )
            return precision and (tool_flat or (first.endswith("_tip") and (terminal_disc or sleeve)))

        use &= np.array(
            [
                not (grip_interface(self.names[i], self.names[j]) or grip_interface(self.names[j], self.names[i]))
                for i, j in zip(a, b, strict=True)
            ]
        )
        self.all_a, self.all_b = a[use], b[use]
        self.a, self.b = a[use & relevant], b[use & relevant]
        self.pair_cache = {}
        self.objects, centers, extents = [], [], []
        for i in range(len(self.names)):
            vertices = d["vertices"][d["vertex_offsets"][i] : d["vertex_offsets"][i + 1]]
            faces = d["faces"][d["face_offsets"][i] : d["face_offsets"][i + 1]]
            mesh = fcl.BVHModel()
            mesh.beginModel(len(vertices), len(faces))
            mesh.addSubModel(vertices, faces)
            mesh.endModel()
            self.objects.append(fcl.CollisionObject(mesh, fcl.Transform()))
            centers.append((vertices.min(0) + vertices.max(0)) / 2)
            extents.append((vertices.max(0) - vertices.min(0)) / 2)
        self.centers, self.extents = np.array(centers), np.array(extents)
        self.world = np.repeat(np.eye(4)[None], len(self.names), axis=0)
        self.request = fcl.CollisionRequest(num_max_contacts=1, enable_contact=False)
        self.set_poses(dict(zip(d["actor_world_names"], d["actor_world"], strict=True)))

    def set_poses(self, poses):
        for name, matrix in poses.items():
            if isinstance(name, (int, np.integer)):
                name = f"source_{int(name):04d}"
            if name not in self.actor_indices:
                continue
            indices = self.actor_indices[name]
            self.world[indices] = matrix
            transform = fcl.Transform(np.asarray(matrix[:3, :3]), np.asarray(matrix[:3, 3]))
            for index in indices:
                self.objects[index].setTransform(transform)

    def score(self, side, extra_actors=()):
        key = (side, tuple(extra_actors))
        if key in self.pair_cache:
            a, b = self.pair_cache[key]
        elif extra_actors:
            a, b = self.all_a, self.all_b
            carried = np.isin(self.actors, extra_actors)
            # The tool and its retained nut form one fixed assembly during
            # these transits. Socket/nut fit is checked by the contact audit.
            active = (self.side[a] == side) | (self.side[b] == side) | carried[a] | carried[b]
            active &= ~(carried[a] & carried[b])
            a, b = a[active], b[active]
            self.pair_cache[key] = a, b
        else:
            a, b = self.a, self.b
            active = (self.side[a] == side) | (self.side[b] == side)
            a, b = a[active], b[active]
            self.pair_cache[key] = a, b
        rotation = self.world[:, :3, :3]
        xyz = np.einsum("nij,nj->ni", rotation, self.centers) + self.world[:, :3, 3]
        extent = np.einsum("nij,nj->ni", abs(rotation), self.extents)
        mask = np.all(extent[a] + extent[b] - abs(xyz[a] - xyz[b]) > 1e-5, axis=1)
        hits = []
        for i, j in zip(a[mask], b[mask], strict=True):
            result = fcl.CollisionResult()
            fcl.collide(self.objects[i], self.objects[j], self.request, result)
            if result.is_collision:
                hits.append((self.names[i], self.names[j]))
        self.last_pairs = hits
        return float(10 * len(hits))
