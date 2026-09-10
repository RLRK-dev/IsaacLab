# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Parameterized actual-triangle branch screen for split ST A/C [m].

Reuses the established FCL BVH/AABB implementation. Results are discrete
surface-intersection observations, not contact forces or physical approval.
"""

import sys
from pathlib import Path

import numpy as np

try:
    import fcl
except ImportError:
    sys.path.insert(0, "/tmp/ur15_op030_fcl")
    import fcl


class BranchMeshes:
    """Read an explicit mesh export and screen articulated actor poses [m].

    Args:
        mesh_file: A/C NPZ produced by export_op030_split_ac_meshes.py.
    """

    def __init__(self, mesh_file: str | Path):
        self.mesh_file = Path(mesh_file)
        with np.load(self.mesh_file, allow_pickle=False) as source:
            data = {key: source[key].copy() for key in source.files}
        self.names, self.nodes, self.actors = data["names"], data["nodes"], data["actors"]
        self.side, self.links, self.roles = data["sides"], data["links"], data["roles"]
        self.fixed_base = data["fixed_base"]
        self.actor_indices = {str(name): np.flatnonzero(self.actors == name) for name in set(self.actors)}
        self.actor_world = dict(zip(data["actor_world_names"].tolist(), data["actor_world"], strict=True))
        self.actor_parent = dict(zip(data["actor_world_names"].tolist(), data["actor_parents"].tolist(), strict=True))
        self.actor_local = dict(zip(data["actor_world_names"].tolist(), data["actor_local"], strict=True))
        self.native_aliases = dict(
            zip(data["actor_native_names"].tolist(), data["actor_world_names"].tolist(), strict=True)
        )
        self.initial_actor_world = {name: matrix.copy() for name, matrix in self.actor_world.items()}
        self.all_a, self.all_b = np.triu_indices(len(self.names), 1)
        a, b = self.all_a, self.all_b
        same_actor = (self.actors[a] == self.actors[b]) & (self.actors[a] != "")
        same_arm = (self.side[a] >= 0) & (self.side[a] == self.side[b])
        adjacent = same_arm & (np.abs(self.links[a] - self.links[b]) <= 1)
        mount = ((self.nodes[a] == 578) & (self.links[b] == 0) & (self.side[b] >= 0)) | (
            (self.nodes[b] == 578) & (self.links[a] == 0) & (self.side[a] >= 0)
        )
        use = ~(same_actor | adjacent | mount)
        self.all_a, self.all_b = a[use], b[use]
        self.exclusion_counts = dict(
            same_actor=int(same_actor.sum()), same_arm_adjacent=int(adjacent.sum()), torso_base_mount=int(mount.sum())
        )
        self.objects, centers, extents = [], [], []
        for index in range(len(self.names)):
            vertices = data["vertices"][data["vertex_offsets"][index] : data["vertex_offsets"][index + 1]]
            triangles = data["faces"][data["face_offsets"][index] : data["face_offsets"][index + 1]]
            mesh = fcl.BVHModel()
            mesh.beginModel(len(vertices), len(triangles))
            mesh.addSubModel(vertices, triangles)
            mesh.endModel()
            self.objects.append(fcl.CollisionObject(mesh, fcl.Transform()))
            centers.append((vertices.min(0) + vertices.max(0)) / 2)
            extents.append((vertices.max(0) - vertices.min(0)) / 2)
        self.centers, self.extents = np.asarray(centers), np.asarray(extents)
        self.world = np.repeat(np.eye(4)[None], len(self.names), axis=0)
        self.request = fcl.CollisionRequest(num_max_contacts=1, enable_contact=False)
        self.pair_cache = {}
        self.contact_pairs = set()
        self.last_pairs = []
        self.set_poses(self.actor_world.copy())

    def _name(self, name) -> str:
        if isinstance(name, (int, np.integer)):
            return f"source_{int(name):04d}"
        return self.native_aliases.get(str(name), str(name))

    def set_actor_parent(self, actor: str, parent: str | None) -> None:
        """Change a carried/installed actor parent while preserving its pose [m]."""
        actor = self._name(actor)
        parent = self._name(parent) if parent else ""
        if actor not in self.actor_world or (parent and parent not in self.actor_world):
            raise KeyError((actor, parent))
        test = parent
        while test:
            if test == actor:
                raise ValueError("Actor parenting cycle")
            test = self.actor_parent[test]
        self.actor_parent[actor] = parent
        self.actor_local[actor] = (
            np.linalg.inv(self.actor_world[parent]) @ self.actor_world[actor]
            if parent
            else self.actor_world[actor].copy()
        )

    def set_poses(self, poses: dict, *, strict: bool = False) -> None:
        """Set canonical world poses and propagate registered child actors [m].

        Integer keys denote original source IDs. Explicit child world poses
        override inherited motion. Detach a part with set_actor_parent on pick.
        """
        updates = {}
        for raw_name, matrix in poses.items():
            name = self._name(raw_name)
            if name not in self.actor_world:
                if strict:
                    raise KeyError(name)
                continue
            matrix = np.asarray(matrix, dtype=float)
            if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
                raise ValueError(f"Invalid transform: {name}")
            updates[name] = matrix
        done, affected = set(), set()

        def update(name):
            if name in done:
                return
            parent = self.actor_parent[name]
            if parent:
                update(parent)
            if name in updates:
                self.actor_world[name] = updates[name].copy()
                self.actor_local[name] = (
                    np.linalg.inv(self.actor_world[parent]) @ updates[name] if parent else updates[name].copy()
                )
                affected.add(name)
            elif parent in affected:
                self.actor_world[name] = self.actor_world[parent] @ self.actor_local[name]
                affected.add(name)
            done.add(name)

        for name in self.actor_world:
            update(name)
        for name in affected:
            indices = self.actor_indices.get(name, ())
            if len(indices) == 0:
                continue
            matrix = self.actor_world[name]
            self.world[indices] = matrix
            transform = fcl.Transform(matrix[:3, :3], matrix[:3, 3])
            for index in indices:
                self.objects[index].setTransform(transform)

    def set_contact_pairs(self, pairs=()) -> None:
        """Set exact mesh-name contact exceptions, with no wildcard masking."""
        names = set(self.names)
        result = set()
        for first, second in pairs:
            if first not in names or second not in names:
                raise KeyError((first, second))
            result.add(tuple(sorted((first, second))))
        self.contact_pairs = result
        self.pair_cache.clear()

    def score(self, side: int | None, extra_actors=(), grasp_actors=(), *, max_hits: int | None = None) -> float:
        """Count selected-arm/carried-part surface intersections [m].

        Args:
            side: 0 left, 1 right, or None for both arms.
            extra_actors: Carried actors whose environment intersections matter.
            grasp_actors: The currently grasped support IDs only. Each enables
                exactly right precision tip versus that support insulator.
            max_hits: Optional early collision stop; None records all pairs.

        Returns:
            Ten times the number of intersections. Zero is a discrete mesh
            observation, never a formal physical-validity verdict.
        """
        if side not in (None, 0, 1):
            raise ValueError(side)
        extra = tuple(sorted(self._name(actor) for actor in extra_actors))
        grasp = tuple(sorted(self._name(actor) for actor in grasp_actors))
        key = (side, extra, grasp)
        if key not in self.pair_cache:
            a, b = self.all_a, self.all_b
            relevant = (self.side >= 0) if side is None else (self.side == side)
            relevant |= np.isin(self.actors, extra)
            use = relevant[a] | relevant[b]
            tip = (self.roles == "precision_tip") & (self.side == 1)
            disc = (self.roles == "support_insulator") & np.isin(self.actors, grasp)
            use &= ~((tip[a] & disc[b]) | (tip[b] & disc[a]))
            if self.contact_pairs:
                use &= np.array(
                    [
                        tuple(sorted((self.names[i], self.names[j]))) not in self.contact_pairs
                        for i, j in zip(a, b, strict=True)
                    ]
                )
            self.pair_cache[key] = a[use], b[use]
        a, b = self.pair_cache[key]
        rotation = self.world[:, :3, :3]
        center = np.einsum("nij,nj->ni", rotation, self.centers) + self.world[:, :3, 3]
        extent = np.einsum("nij,nj->ni", abs(rotation), self.extents)
        overlap = np.all(extent[a] + extent[b] - abs(center[a] - center[b]) > 1e-5, axis=1)
        hits = []
        for first, second in zip(a[overlap], b[overlap], strict=True):
            result = fcl.CollisionResult()
            fcl.collide(self.objects[first], self.objects[second], self.request, result)
            if result.is_collision:
                hits.append((str(self.names[first]), str(self.names[second])))
                if max_hits and len(hits) >= max_hits:
                    break
        self.last_pairs = hits
        return float(10 * len(hits))
