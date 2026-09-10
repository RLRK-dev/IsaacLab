# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Inspect every saved A frame against a later static mesh, without rewriting banks [m, s]."""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_motion import SIDES
from op030_split_ac_meshes import fcl
from op030_support_plan_v04 import PlanningContext


def digest(path: Path) -> str:
    """Read a file digest without changing its contents."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def mesh_delta(baseline: Path, candidate: Path) -> dict:
    """Compare actual mesh coordinates, topology, actor transforms and roles [m]."""
    arrays = []
    for path in (baseline, candidate):
        with np.load(path, allow_pickle=False) as source:
            arrays.append({name: source[name] for name in source.files})
    old, new = arrays
    old_indices = {str(name): index for index, name in enumerate(old["names"])}
    actor_records = []
    for data in arrays:
        actor_records.append(
            {
                str(name): {
                    key: data[key][index]
                    for key in ("actor_world", "actor_parents", "actor_local", "actor_native_names")
                }
                for index, name in enumerate(data["actor_world_names"])
            }
        )
    changed, same = [], []
    for index, name in enumerate(new["names"]):
        name = str(name)
        if name not in old_indices:
            changed.append(dict(name=name, reasons=["added"]))
            continue
        previous = old_indices[name]
        reasons = []
        for key, offsets in (("vertices", "vertex_offsets"), ("faces", "face_offsets")):
            before = old[key][old[offsets][previous] : old[offsets][previous + 1]]
            after = new[key][new[offsets][index] : new[offsets][index + 1]]
            if not np.array_equal(before, after):
                reasons.append(key)
        for key in ("actors", "nodes", "sides", "links", "roles"):
            if old[key][previous] != new[key][index]:
                reasons.append(key)
        actor = str(new["actors"][index])
        if actor and old["actors"][previous] == actor:
            for key, value in actor_records[1][actor].items():
                if not np.array_equal(actor_records[0][actor][key], value):
                    reasons.append(key)
        if not np.array_equal(old["fixed_base"], new["fixed_base"]):
            reasons.append("fixed_base")
        if reasons:
            changed.append(dict(name=name, reasons=reasons))
        else:
            same.append(name)
    return dict(
        baseline_mesh=str(baseline),
        candidate_mesh=str(candidate),
        baseline_count=len(old["names"]),
        candidate_count=len(new["names"]),
        unchanged_count=len(same),
        unchanged_names=same,
        changed=changed,
        removed_names=sorted(set(old_indices) - set(new["names"].tolist())),
        comparison="Exact array equality, with empty static actors represented by their baked world vertices",
    )


class OutsideSupportCheck:
    """Check world-space supports outside the station export against its tracked actors [m]."""

    def __init__(self, path: Path, screen, bank_objects: np.ndarray):
        with np.load(path, allow_pickle=False) as source:
            data = {key: source[key] for key in source.files}
        self.names, self.objects, centers, extents = [], [], [], []
        for index, name in enumerate(data["names"]):
            if name in screen.names:
                continue
            vertices = data["vertices"][data["vertex_offsets"][index] : data["vertex_offsets"][index + 1]]
            faces = data["faces"][data["face_offsets"][index] : data["face_offsets"][index + 1]]
            mesh = fcl.BVHModel()
            mesh.beginModel(len(vertices), len(faces))
            mesh.addSubModel(vertices, faces)
            mesh.endModel()
            self.names.append(str(name))
            self.objects.append(fcl.CollisionObject(mesh, fcl.Transform()))
            centers.append((vertices.min(0) + vertices.max(0)) / 2)
            extents.append((vertices.max(0) - vertices.min(0)) / 2)
        self.centers, self.extents = np.asarray(centers), np.asarray(extents)
        self.indices = np.flatnonzero((screen.side >= 0) | np.isin(screen.actors, bank_objects))
        self.minimum_aabb_separation_m = float("inf")
        self.aabb_overlap_pairs = 0

    def query(self, screen) -> list[tuple[str, str]]:
        """Use the same BVH and broad-phase convention for each saved world pose [m]."""
        if not self.names:
            return []
        indices = self.indices
        world = screen.world[indices]
        centers = np.einsum("nij,nj->ni", world[:, :3, :3], screen.centers[indices]) + world[:, :3, 3]
        extents = np.einsum("nij,nj->ni", abs(world[:, :3, :3]), screen.extents[indices])
        gaps = abs(centers[:, None] - self.centers[None]) - (extents[:, None] + self.extents[None])
        self.minimum_aabb_separation_m = min(self.minimum_aabb_separation_m, float(gaps.max(axis=2).min()))
        first, second = np.where(np.all(gaps < -1e-5, axis=2))
        self.aabb_overlap_pairs += len(first)
        hits = []
        for a, b in zip(first, second, strict=True):
            result = fcl.CollisionResult()
            fcl.collide(screen.objects[indices[a]], self.objects[b], screen.request, result)
            if result.is_collision:
                hits.append((str(screen.names[indices[a]]), self.names[b]))
        return hits


def main() -> None:
    """Use the existing simultaneous-FK checker with saved joints [rad] and time [s]."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh_file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bank", type=Path, default=ROOT / "data/op030_split_a_motion_v04.npz")
    parser.add_argument("--baseline_mesh", type=Path, help="Limit new FCL queries to the exact mesh differences")
    parser.add_argument("--baseline_audit", type=Path, default=ROOT / "audit/op030_split_a_motion_v04.json")
    parser.add_argument("--extra_world_mesh", type=Path, help="Check supports excluded from the local mesh export")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Preserve the existing audit: {args.output}")
    source_names = (
        "op030_support_plan_v04.py",
        "op030_support_motion_v04.py",
        "op030_fastener_operations_v04.py",
        "op030_split_a_plan.py",
        "op030_split_ac_meshes.py",
        "op030_split_support_motion.py",
        "op030_split_fastening_motion.py",
        "op030_split_tools.py",
        "solve_op030_motion.py",
        "op030_motion.py",
        "op030_definition.py",
    )
    inputs = [args.bank, args.mesh_file, args.mesh_file.with_suffix(".json")]
    if args.baseline_mesh:
        inputs += [args.baseline_mesh, args.baseline_mesh.with_suffix(".json"), args.baseline_audit]
    if args.extra_world_mesh:
        inputs += [args.extra_world_mesh, args.extra_world_mesh.with_suffix(".json")]
    inputs += [ROOT / "scripts" / name for name in source_names]
    hashes = {str(path): digest(path) for path in inputs}
    with np.load(args.bank, allow_pickle=False) as saved:
        bank = {
            name: saved[name]
            for name in (
                "times",
                "author_times",
                "joints",
                "node_ids",
                "poses",
                "tools",
                "grips",
                "spindle_angles",
                "object_names",
            )
        }
    began = datetime.now().astimezone().isoformat()
    context = PlanningContext(args.mesh_file)
    differences = None
    if args.baseline_mesh:
        previous = json.loads(args.baseline_audit.read_text())
        if previous["candidate_sha256"] != digest(args.bank) or previous["failures"] or previous["fcl_hits"]:
            raise ValueError("The saved bank does not have a clear baseline full-frame audit")
        if digest(args.baseline_mesh) not in previous["verification_input_sha256"].values():
            raise ValueError("The selected baseline mesh was not used by the baseline full-frame audit")
        for name, value in previous["source_sha256"].items():
            if digest(ROOT / "scripts" / name) != value:
                raise ValueError(f"Original full-frame source changed: {name}")
        differences = mesh_delta(args.baseline_mesh, args.mesh_file)
        changed = np.isin(context.screen.names, [row["name"] for row in differences["changed"]])
        a, b = context.screen.all_a, context.screen.all_b
        selected = changed[a] | changed[b]
        context.screen.all_a, context.screen.all_b = a[selected], b[selected]
        context.screen.pair_cache.clear()
        print("A_MESH_DIFFERENCES", differences["unchanged_count"], len(differences["changed"]), flush=True)
    outside = (
        OutsideSupportCheck(args.extra_world_mesh, context.screen, bank["object_names"])
        if args.extra_world_mesh
        else None
    )
    hits, failures = [], []
    maxima = dict(node_matrix_delta=0.0, grip_delta=0.0, spindle_angle_delta_rad=0.0)
    for index, (time, q) in enumerate(zip(bank["author_times"], bank["joints"], strict=True)):
        target, _, _, _ = context.state(float(time))
        score, pairs = context.query(float(time), q, override_free=True)
        outside_hits = outside.query(context.screen) if outside else []
        score += len(outside_hits) * 10
        pairs.extend(outside_hits)
        captures = {577: target["root"], 578: target["root"]}
        for side in SIDES:
            captures.update(context.robots[side][1].poses)
        current = np.asarray([captures[int(node)] for node in bank["node_ids"]])
        deltas = dict(
            node_matrix_delta=float(np.max(np.abs(current - bank["poses"][index]))),
            grip_delta=float(np.max(np.abs(target["grips"] - bank["grips"][index]))),
            spindle_angle_delta_rad=float(np.max(np.abs(target["spindle_angles"] - bank["spindle_angles"][index]))),
        )
        for key, value in deltas.items():
            maxima[key] = max(maxima[key], value)
        if max(deltas.values()) > 1e-9:
            failures.append(dict(frame=index + 1, **deltas))
        if score:
            hits.append(
                dict(
                    frame=index + 1,
                    display_time_s=float(bank["times"][index]),
                    author_time_s=float(time),
                    label=target["label"],
                    pairs=pairs,
                )
            )
        if index % 300 == 0:
            print("A_SAVED_BANK_MESH", index, len(bank["times"]), len(failures), len(hits), flush=True)
    unchanged = hashes == {str(path): digest(path) for path in inputs}
    metadata = json.loads(args.mesh_file.with_suffix(".json").read_text())
    result = dict(
        observed_at=began,
        completed_at=datetime.now().astimezone().isoformat(),
        script_sha256=digest(Path(__file__)),
        inputs_sha256=hashes,
        inputs_unchanged=unchanged,
        bank=str(args.bank),
        bank_sha256=hashes[str(args.bank)],
        verification_mesh=str(args.mesh_file),
        verification_mesh_sha256=hashes[str(args.mesh_file)],
        verification_native=metadata.get("native_input"),
        verification_native_sha256=metadata.get("native_input_sha256"),
        frames=len(bank["times"]),
        fps=30,
        mesh_count=metadata["meshes"],
        triangle_count=metadata["triangles"],
        maxima=maxima,
        pose_identity_failures=failures,
        fcl_hits=hits,
        passed=unchanged and not failures and not hits,
        additional_contact_exceptions=[],
        bank_rewritten=False,
        geometry_modified=False,
        mesh_difference_comparison=differences,
        baseline_full_frame_audit=str(args.baseline_audit) if args.baseline_mesh else None,
        outside_supports=None
        if outside is None
        else dict(
            names=outside.names,
            tracked_mesh_count=len(outside.indices),
            minimum_axis_aabb_separation_m=outside.minimum_aabb_separation_m,
            aabb_overlap_pair_samples=outside.aabb_overlap_pairs,
        ),
        scope=(
            "All saved A native-frame joints through the reused original FK/simultaneous actor mesh checker. "
            + (
                "FCL limited to changed/added mesh pairs; unchanged geometry covered by pinned baseline audit. "
                if differences is not None
                else ""
            )
            + "Includes both arms/tools/cameras, held support and held fastener. "
            "Feeder internal mechanism and transport checks are separate. No formal physical-validity verdict."
        ),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("A_SAVED_BANK_MESH_COMPLETE", len(bank["times"]), len(failures), len(hits), unchanged, flush=True)
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
