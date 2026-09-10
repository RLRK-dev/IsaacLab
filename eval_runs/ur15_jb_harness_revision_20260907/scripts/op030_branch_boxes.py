# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Conservative native-component OBB preference, not an acceptance test [m]."""

import numpy as np
from op030_definition import ROOT


class BranchBoxes:
    def __init__(self):
        with np.load(ROOT / "data/op030_branch_boxes.npz") as data:
            self.nodes, self.local, self.extents = data["nodes"].copy(), data["matrices"].copy(), data["extents"].copy()
            self.fixed_base = data["fixed_base"].copy()
        self.indices = {node: np.flatnonzero(self.nodes == node) for node in np.unique(self.nodes)}
        self.side = np.where(self.nodes < 1000, -1, np.where(self.nodes < 1084, 0, 1))
        local_node = self.nodes - np.where(self.side == 0, 1046, 1086)
        links = np.searchsorted([3, 5, 10, 15, 18, 20, 21, 38], local_node, side="right")
        a, b = np.triu_indices(len(self.nodes), 1)
        nonadjacent = (self.side[a] == self.side[b]) & (self.side[a] != -1) & (abs(links[a] - links[b]) > 1)
        other = self.side[a] != self.side[b]
        # Boxes around the fixed base and immediately joined shoulder include
        # space outside the curved shells. Exclude these only from branch
        # preference; the native triangle audit keeps its narrower mount rule.
        joined = [1046, 1047, 1048, 1049, 1086, 1087, 1088, 1089]
        mount = ((self.nodes[a] == 578) & np.isin(self.nodes[b], joined)) | (
            (self.nodes[b] == 578) & np.isin(self.nodes[a], joined)
        )
        use = (nonadjacent | other) & ~mount
        self.a, self.b = a[use], b[use]
        self.world = self.local.copy()

    def set_poses(self, poses):
        for node, matrix in poses.items():
            if node in self.indices:
                selection = self.indices[node]
                self.world[selection] = matrix @ self.local[selection]

    def score(self, side):
        active = (self.side[self.a] == side) | (self.side[self.b] == side)
        a, b = self.a[active], self.b[active]
        rotation = self.world[:, :3, :3]
        xyz = self.world[:, :3, 3]
        # The sphere/AABB broad phase only removes separated pairs.
        extent = np.einsum("nij,nj->ni", abs(rotation), self.extents)
        broad = np.all(extent[a] + extent[b] - abs(xyz[a] - xyz[b]) > 0.0001, axis=1)
        a, b = a[broad], b[broad]
        if not len(a):
            return 0.0
        aa, bb = rotation[a].transpose(0, 2, 1), rotation[b].transpose(0, 2, 1)
        cross = np.cross(aa[:, :, None, :], bb[:, None, :, :]).reshape(-1, 9, 3)
        axes = np.concatenate((aa, bb, cross), axis=1)
        norm = np.linalg.norm(axes, axis=2)
        axes /= np.maximum(norm[:, :, None], 1e-12)
        radii_a = np.einsum("nki,nij->nkj", axes, rotation[a])
        radii_b = np.einsum("nki,nij->nkj", axes, rotation[b])
        overlaps = (
            np.einsum("nkj,nj->nk", abs(radii_a), self.extents[a])
            + np.einsum("nkj,nj->nk", abs(radii_b), self.extents[b])
            - abs(np.einsum("nki,ni->nk", axes, xyz[a] - xyz[b]))
        )
        overlaps[norm < 1e-6] = np.inf
        depth = overlaps.min(1)
        positive = depth[depth > 0.00025]
        self.last_pairs = [
            (int(self.nodes[i]), int(self.nodes[j]), float(d))
            for i, j, d in zip(a, b, depth, strict=True)
            if d > 0.00025
        ]
        return float(len(positive) * 10 + positive.sum() * 100)
