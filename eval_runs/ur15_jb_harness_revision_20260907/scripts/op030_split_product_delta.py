# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Screen product-local geometry changes against saved A and transfer poses [m]."""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_split_ac_meshes import BranchMeshes, fcl

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = "JB_OP020_UID001_B01_B02_B03_p00"
A_MESH = ROOT / "data/op030_split_a_transfer_v01_meshes.npz"
A_BANK = ROOT / "data/op030_split_a_motion_v03.npz"
TRANSFERS = {
    "entry": ROOT / "analysis/split_layout_entry_payload_v05_meshes.npz",
    "a_to_b": ROOT / "analysis/split_layout_a_transfer_v01_payload_meshes.npz",
}


def digest(path: Path) -> str:
    """Return a file SHA-256."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path: Path) -> dict:
    """Read a selected mesh/motion NPZ without object deserialization."""
    with np.load(path, allow_pickle=False) as source:
        return {key: source[key].copy() for key in source.files}


def mesh_points(data: dict, index: int) -> tuple[np.ndarray, np.ndarray]:
    """Return one local triangle mesh [m]."""
    vertices = data["vertices"][data["vertex_offsets"][index] : data["vertex_offsets"][index + 1]]
    faces = data["faces"][data["face_offsets"][index] : data["face_offsets"][index + 1]]
    return vertices, faces


class MeshGroup:
    """Retain BVHs and local AABBs for selected unchanged surfaces [m]."""

    def __init__(self, data: dict, stretches: np.ndarray | None = None):
        self.names = data["names"].astype(str)
        self.objects, centers, extents = [], [], []
        for index in range(len(self.names)):
            vertices, faces = mesh_points(data, index)
            if stretches is not None:
                vertices = vertices @ stretches[index].T
            model = fcl.BVHModel()
            model.beginModel(len(vertices), len(faces))
            model.addSubModel(vertices, faces)
            model.endModel()
            self.objects.append(fcl.CollisionObject(model, fcl.Transform()))
            centers.append((vertices.min(0) + vertices.max(0)) / 2)
            extents.append((vertices.max(0) - vertices.min(0)) / 2)
        self.centers, self.extents = np.asarray(centers), np.asarray(extents)


class DeltaCheck:
    """Check changed product-local surfaces without broad contact exemptions [m]."""

    def __init__(self, delta: dict, context, removed: list[str]):
        self.delta = MeshGroup(delta)
        self.context = context
        self.indices = np.flatnonzero(~np.isin(context.names, removed))
        self.removed_present = sorted(set(context.names).intersection(removed))
        self.request = fcl.CollisionRequest(num_max_contacts=4, enable_contact=True)
        self.pairs = {}
        self.hit_frames = set()
        self.narrow_phase_queries = 0
        self.maximum_rotation_residual = 0.0

    def sample(self, frame: int, time: float, product: np.ndarray, worlds: np.ndarray) -> None:
        """Check one saved frame; positions [m], time [s]."""
        rotations = worlds[:, :3, :3]
        residual = float(np.max(abs(np.swapaxes(rotations, 1, 2) @ rotations - np.eye(3))))
        self.maximum_rotation_residual = max(self.maximum_rotation_residual, residual)
        if residual > 2e-6:
            raise ValueError(f"Nonrigid transform supplied to delta FCL: {residual}")
        centers = np.einsum("nij,nj->ni", rotations, self.context.centers) + worlds[:, :3, 3]
        extents = np.einsum("nij,nj->ni", abs(rotations), self.context.extents)
        delta_centers = self.delta.centers @ product[:3, :3].T + product[:3, 3]
        delta_extents = self.delta.extents @ abs(product[:3, :3]).T
        selected = self.indices
        for first, name in enumerate(self.delta.names):
            self.delta.objects[first].setTransform(fcl.Transform(product[:3, :3], product[:3, 3]))
            candidates = selected[
                np.all(
                    extents[selected] + delta_extents[first] - abs(centers[selected] - delta_centers[first]) > 1e-5,
                    axis=1,
                )
            ]
            for second in candidates:
                matrix = worlds[second]
                self.context.objects[second].setTransform(fcl.Transform(matrix[:3, :3], matrix[:3, 3]))
                result = fcl.CollisionResult()
                fcl.collide(self.delta.objects[first], self.context.objects[second], self.request, result)
                self.narrow_phase_queries += 1
                if not result.is_collision:
                    continue
                self.hit_frames.add(frame)
                key = (str(name), str(self.context.names[second]))
                row = self.pairs.setdefault(
                    key,
                    dict(
                        changed=key[0],
                        other=key[1],
                        frames=[],
                        first_time_s=time,
                        last_time_s=time,
                        maximum_depth_m=0.0,
                        first_contacts=[],
                    ),
                )
                row["frames"].append(frame)
                row["last_time_s"] = time
                contacts = [
                    dict(
                        changed_face=int(c.b1),
                        other_face=int(c.b2),
                        point_m=np.asarray(c.pos).tolist(),
                        depth_m=float(c.penetration_depth),
                    )
                    for c in result.contacts
                ]
                row["maximum_depth_m"] = max([row["maximum_depth_m"], *(c["depth_m"] for c in contacts)])
                if not row["first_contacts"]:
                    row["first_contacts"] = contacts

    def record(self) -> dict:
        """Return raw auxiliary observations, without a physical verdict."""
        return dict(
            changed_meshes=self.delta.names.tolist(),
            context_meshes=len(self.indices),
            removed_replaced_meshes=self.removed_present,
            hit_frames=sorted(self.hit_frames),
            pairs=list(self.pairs.values()),
            narrow_phase_queries=self.narrow_phase_queries,
            maximum_rotation_residual=self.maximum_rotation_residual,
            contact_exemptions=[],
            scope=(
                "Changed meshes versus retained context, including other product parts; "
                "internal changed-to-changed assembly interfaces are recorded by their builder"
            ),
            formal_physical_validity_verdict=None,
        )


def check_a(delta: dict, removed: list[str]) -> dict:
    """Reuse every saved A pose and permanent spindle orientation [m, rad, s]."""
    screen = BranchMeshes(A_MESH)
    check = DeltaCheck(delta, screen, removed)
    bank = load(A_BANK)
    metadata = json.loads(A_MESH.with_suffix(".json").read_text())
    driver = metadata["fixed_tools"]["OP030A_M4"]
    flange_to_tcp = np.asarray(driver["flange_to_tcp"])
    product_index = bank["object_names"].tolist().index("JB_OP020_UID001")
    flange_index = bank["node_ids"].tolist().index(1067)
    for index, time in enumerate(bank["times"]):
        screen.set_poses(dict(zip(bank["object_names"], bank["object_poses"][index], strict=True)))
        screen.set_poses(dict(zip(bank["node_ids"], bank["poses"][index], strict=True)))
        angle = bank["spindle_angles"][index, 0]
        rotation = np.eye(4)
        rotation[:2, :2] = [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
        screen.set_poses({driver["spindle"]: bank["poses"][index, flange_index] @ flange_to_tcp @ rotation})
        product = bank["object_poses"][index, product_index]
        check.sample(index + 1, float(time), product, screen.world)
        if index % 600 == 0:
            print("A_PRODUCT_DELTA", index, len(bank["times"]), len(check.hit_frames), flush=True)
    return dict(
        **check.record(),
        bank=str(A_BANK),
        bank_sha256=digest(A_BANK),
        context=str(A_MESH),
        context_sha256=digest(A_MESH),
        frames=len(bank["times"]),
        pose_source="Saved original-FK poses and saved object poses; no IK or replanning",
    )


def check_transfer(delta: dict, removed: list[str], kind: str) -> dict:
    """Reuse saved full-payload transfer tracks, baking constant stretch [m, s]."""
    source = TRANSFERS[kind]
    data = load(source)
    matrices = data["matrices"].copy()
    left, _, right = np.linalg.svd(matrices[..., :3, :3])
    sign = np.linalg.det(left @ right)
    left[..., :, -1] *= np.where(sign < 0, -1.0, 1.0)[..., None]
    rotations = left @ right
    stretch = np.swapaxes(rotations, -1, -2) @ matrices[..., :3, :3]
    variation = float(np.max(abs(stretch - stretch[:1])))
    if variation > 2e-6:
        raise ValueError("A transfer contains time-varying stretch")
    matrices[..., :3, :3] = rotations
    # The unchanged housing mesh is stored directly in product coordinates.
    # Check every vertex and face against the A export before reusing its pose
    # as the product reference; do not infer this from a mesh name alone.
    reference = data["names"].tolist().index(REFERENCE)
    baseline = load(A_MESH)
    other = baseline["names"].tolist().index(REFERENCE)
    for actual, expected in zip(mesh_points(data, reference), mesh_points(baseline, other), strict=True):
        np.testing.assert_allclose(actual, expected, atol=1e-7, rtol=0)
    np.testing.assert_allclose(stretch[0, reference], np.eye(3), atol=1e-7, rtol=0)
    context = MeshGroup(data, stretch[0])
    check = DeltaCheck(delta, context, removed)
    for index, time in enumerate(data["times"]):
        check.sample(index + 1, float(time), matrices[index, reference], matrices[index])
        if index % 60 == 0:
            print("TRANSFER_PRODUCT_DELTA", kind, index, len(data["times"]), len(check.hit_frames), flush=True)
    return dict(
        **check.record(),
        context=str(source),
        context_sha256=digest(source),
        frames=len(data["times"]),
        product_reference_mesh=REFERENCE,
        maximum_stretch_variation=variation,
        affine_baked_meshes=data["names"][np.max(abs(stretch[0] - np.eye(3)), axis=(1, 2)) > 1e-6].tolist(),
    )


def main() -> None:
    """Run one explicitly selected geometry delta against preserved trajectories."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--delta", type=Path, required=True, help="Meshes with all vertices in the active product frame"
    )
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--removed_key", default="removed_old_meshes")
    parser.add_argument("--mode", choices=("a", "entry", "a_to_b"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    metadata = json.loads(args.metadata.read_text())
    delta_sha, metadata_sha = digest(args.delta), digest(args.metadata)
    removed = metadata[args.removed_key]
    delta = load(args.delta)
    report = check_a(delta, removed) if args.mode == "a" else check_transfer(delta, removed, args.mode)
    if digest(args.delta) != delta_sha or digest(args.metadata) != metadata_sha:
        raise ValueError("The delta or its metadata changed while the check was running")
    report.update(
        observed_at=datetime.now().astimezone().isoformat(),
        delta=str(args.delta),
        delta_sha256=digest(args.delta),
        metadata=str(args.metadata),
        metadata_sha256=digest(args.metadata),
        checker_sha256=digest(Path(__file__)),
    )
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PRODUCT_DELTA_COMPLETE", args.mode, report["frames"], len(report["hit_frames"]), flush=True)


if __name__ == "__main__":
    main()
