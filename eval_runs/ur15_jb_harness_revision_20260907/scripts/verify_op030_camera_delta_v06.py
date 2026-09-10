# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Compare saved natives around an explicit review-camera-only edit [m, rad, s].

Reuse the mesh/F-curve readback approach from verify_feeder_prefix_reuse_v11
and verify_continuous_blend. Read all stored keys, handles and interpolation,
driver targets, hierarchy, modifiers, mesh attributes, shape keys and shader
settings. No native is saved and no collision calculation is repeated.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/op030_candidate_8674_v06"
OLD_SHA = "8674c2483ac1fe7e3dc42e6b1d14fdc4919f28818784de4f53f878477714d338"
MATRIX_TOLERANCE = 2e-6


def digest(path: Path) -> str:
    """Read the exact file SHA256."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def plain(value):
    """Normalize RNA primitive values without serializing runtime pointers."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bpy.types.ID):
        return {"id": value.name_full, "type": value.bl_rna.identifier}
    if isinstance(value, set):
        return sorted(value)
    if hasattr(value, "to_dict"):
        return plain(value.to_dict())
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if hasattr(value, "to_list"):
        return plain(value.to_list())
    return [plain(item) for item in value]


def settings(block, *, depth: int = 1, exclude: tuple[str, ...] = ()) -> dict:
    """Read persistent RNA settings, with explicit ID references preserved."""
    output = {}
    for prop in block.bl_rna.properties:
        key = prop.identifier
        if key in exclude or key in {"rna_type", "name", "name_full"} or prop.is_readonly:
            continue
        value = getattr(block, key)
        if prop.type in {"BOOLEAN", "INT", "FLOAT", "STRING", "ENUM"}:
            output[key] = plain(value)
        elif prop.type == "POINTER":
            if value is None or isinstance(value, bpy.types.ID):
                output[key] = plain(value)
            elif depth:
                output[key] = dict(
                    rna_type=value.bl_rna.identifier,
                    name=getattr(value, "name", None),
                    settings=settings(value, depth=depth - 1),
                )
    return output


class Snapshot:
    """Read model state and stored animation fields [m, rad, native frames]."""

    def __init__(self, path: Path, camera_names: set[str]):
        self.path = path
        self.records = {}
        self.arrays = {}
        self.cameras = {}
        self.counts = Counter()
        self.seen_actions = set()
        self.seen_shapes = set()
        self.read(path, camera_names)

    def array(self, key: str, values: np.ndarray) -> None:
        """Retain an exact numeric field, including native units and shape."""
        if key in self.arrays:
            raise ValueError("Duplicate array key: " + key)
        self.arrays[key] = np.ascontiguousarray(values)

    def field(self, key: str, collection, prop: str, width: int, dtype=np.float32) -> None:
        """Read an RNA collection field without lossy text conversion."""
        values = np.empty((len(collection), width), dtype=dtype)
        collection.foreach_get(prop, values.ravel())
        self.array(key, values)

    def animation(self, key: str, block) -> None:
        """Read every animation key and driver, retaining all key times [frames]."""
        animation = getattr(block, "animation_data", None)
        detached = isinstance(block, bpy.types.Action)
        if not animation and not detached:
            self.records[key] = None
            return
        if animation and animation.nla_tracks:
            raise ValueError("NLA is outside this bounded native comparison: " + key)
        rows = []
        action = block if detached else animation.action
        if action:
            self.seen_actions.add(action.name)
        curves = list(action.fcurves) if action else []
        curves += list(animation.drivers) if animation else []
        for index, curve in enumerate(curves):
            ck = f"{key}/curve/{index}"
            entry = dict(settings=settings(curve), data_path=curve.data_path, array_index=curve.array_index)
            points = curve.keyframe_points
            for prop in ("co", "handle_left", "handle_right"):
                self.field(ck + "/" + prop, points, prop, 2)
            for prop in ("amplitude", "back", "period"):
                self.field(ck + "/" + prop, points, prop, 1)
            for prop in ("interpolation", "easing", "type", "handle_left_type", "handle_right_type"):
                values = [getattr(point, prop) for point in points]
                codes = sorted(set(values))
                lookup = {value: i for i, value in enumerate(codes)}
                entry[prop + "_codes"] = codes
                self.array(ck + "/" + prop, np.asarray([lookup[value] for value in values], dtype=np.uint8))
            self.field(ck + "/samples", curve.sampled_points, "co", 2)
            entry["modifiers"] = [settings(modifier) for modifier in curve.modifiers]
            if curve.driver:
                entry["driver"] = settings(curve.driver)
                entry["driver_variables"] = [
                    dict(settings=settings(variable), targets=[settings(target) for target in variable.targets])
                    for variable in curve.driver.variables
                ]
            rows.append(entry)
            self.counts["fcurves"] += 1
            self.counts["keyframe_points"] += len(points)
            self.counts["driver_fcurves"] += int(bool(curve.driver))
        self.records[key] = dict(
            action=action.name if action else None, settings=settings(animation) if animation else {}, curves=rows
        )

    def mesh(self, mesh) -> None:
        """Read local coordinates, topology, attributes and all shape keys [m]."""
        key = "mesh/" + mesh.name
        if key in self.records:
            return
        self.counts["meshes"] += 1
        self.records[key] = dict(settings=settings(mesh), materials=[plain(mat) for mat in mesh.materials])
        self.field(key + "/vertices", mesh.vertices, "co", 3)
        self.field(key + "/edges", mesh.edges, "vertices", 2, np.int32)
        self.field(key + "/loops", mesh.loops, "vertex_index", 1, np.int32)
        for prop in ("loop_start", "loop_total", "material_index", "use_smooth"):
            self.field(key + "/polygons/" + prop, mesh.polygons, prop, 1, np.int32)
        for attribute in mesh.attributes:
            ak = key + "/attribute/" + attribute.name
            self.records[ak] = dict(domain=attribute.domain, data_type=attribute.data_type)
            if len(attribute.data):
                item = attribute.data[0]
                fields = [
                    prop
                    for prop in item.bl_rna.properties
                    if prop.identifier != "rna_type" and prop.type in {"FLOAT", "INT", "BOOLEAN"}
                ]
                for prop in fields:
                    self.field(
                        ak + "/" + prop.identifier,
                        attribute.data,
                        prop.identifier,
                        prop.array_length if prop.is_array else 1,
                        np.float32 if prop.type == "FLOAT" else np.int32,
                    )
        self.animation(key + "/animation", mesh)
        shape = mesh.shape_keys
        if shape:
            self.records[key + "/shape_key_id"] = shape.name
            self.shape(shape)

    def shape(self, shape) -> None:
        """Read all linked or retained shape-key blocks and their coordinates [m]."""
        if shape.name in self.seen_shapes:
            return
        self.seen_shapes.add(shape.name)
        key = "shape_key/" + shape.name
        self.counts["shape_key_datablocks"] += 1
        self.records[key] = settings(shape)
        for block in shape.key_blocks:
            sk = key + "/shape/" + block.name
            self.records[sk] = settings(block)
            self.records[sk]["relative_key_name"] = block.relative_key.name if block.relative_key else None
            self.field(sk + "/coordinates", block.data, "co", 3)
            self.counts["shape_key_blocks"] += 1
        self.animation(key + "/animation", shape)

    def curve(self, curve) -> None:
        """Read curve geometry, bevel settings and spline controls [m]."""
        key = "curve/" + curve.name
        if key in self.records:
            return
        self.records[key] = dict(settings=settings(curve), materials=[plain(mat) for mat in curve.materials])
        for index, spline in enumerate(curve.splines):
            sk = key + f"/spline/{index}"
            self.records[sk] = dict(settings=settings(spline), type=spline.type)
            for prop in ("co", "radius", "tilt", "weight_softbody"):
                self.field(sk + "/points/" + prop, spline.points, prop, 4 if prop == "co" else 1)
            for prop in ("co", "handle_left", "handle_right", "radius", "tilt"):
                self.field(
                    sk + "/bezier/" + prop,
                    spline.bezier_points,
                    prop,
                    3 if prop in {"co", "handle_left", "handle_right"} else 1,
                )
            self.records[sk + "/handles"] = [
                [point.handle_left_type, point.handle_right_type] for point in spline.bezier_points
            ]
        self.animation(key + "/animation", curve)

    def nodes(self, key: str, tree) -> None:
        """Read shader defaults, links and animation without evaluating lighting."""
        if not tree:
            self.records[key] = None
            return
        rows = []
        for node in sorted(tree.nodes, key=lambda item: item.name):
            rows.append(
                dict(
                    name=node.name,
                    type=node.bl_idname,
                    settings=settings(node),
                    inputs=[
                        dict(name=socket.name, identifier=socket.identifier, settings=settings(socket))
                        for socket in node.inputs
                    ],
                    outputs=[
                        dict(name=socket.name, identifier=socket.identifier, settings=settings(socket))
                        for socket in node.outputs
                    ],
                )
            )
        self.records[key] = dict(
            nodes=rows,
            links=sorted(
                (link.from_node.name, link.from_socket.identifier, link.to_node.name, link.to_socket.identifier)
                for link in tree.links
            ),
        )
        self.animation(key + "/animation", tree)

    def read(self, path: Path, camera_names: set[str]) -> None:
        """Read saved fields at frame 1; never write the native."""
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        scene.frame_set(1)
        if scene.rigidbody_world:
            raise ValueError("Unexpected physical simulation world")
        if not camera_names <= set(scene.objects.keys()):
            raise ValueError("An allowed review camera is absent")
        self.records["scene"] = dict(
            settings=settings(scene, exclude=("camera", "frame_current", "frame_subframe")),
            frame_start=scene.frame_start,
            frame_end=scene.frame_end,
            frame_step=scene.frame_step,
            render=settings(scene.render),
            view=settings(scene.view_settings),
            display=settings(scene.display_settings),
            units=settings(scene.unit_settings),
            cycles=settings(scene.cycles),
            properties=plain(dict(scene.items())),
            world=plain(scene.world),
        )
        self.animation("scene/animation", scene)
        self.nodes("scene/compositor", scene.node_tree)
        for obj in sorted(scene.objects, key=lambda item: item.name):
            self.counts[obj.type] += 1
            key = "object/" + obj.name
            data = dict(
                type=obj.type,
                parent=plain(obj.parent),
                data=plain(obj.data),
                settings=settings(
                    obj, exclude=("matrix_world", "matrix_local", "matrix_basis", "matrix_parent_inverse")
                ),
                properties=plain(dict(obj.items())),
                collections=sorted(c.name for c in obj.users_collection),
                modifiers=[settings(modifier) for modifier in obj.modifiers],
                constraints=[settings(constraint) for constraint in obj.constraints],
                material_slots=[dict(link=slot.link, material=plain(slot.material)) for slot in obj.material_slots],
                vertex_groups=[
                    dict(name=group.name, index=group.index, lock_weight=group.lock_weight)
                    for group in obj.vertex_groups
                ],
            )
            if obj.name in camera_names:
                if obj.type != "CAMERA" or not obj.name.startswith("Review_OP030_"):
                    raise ValueError("Allowed camera is not an engineering review camera")
                self.cameras[obj.name] = dict(
                    object=data,
                    camera=settings(obj.data),
                    world=np.asarray(obj.matrix_world).tolist(),
                    parent_inverse=np.asarray(obj.matrix_parent_inverse).tolist(),
                )
                if obj.children:
                    raise ValueError("Review camera unexpectedly parents scene objects")
                self.animation("review_camera/" + obj.name + "/animation", obj)
                self.animation("review_camera/" + obj.name + "/data_animation", obj.data)
                continue
            self.records[key] = data
            for prop in ("matrix_world", "matrix_local", "matrix_basis", "matrix_parent_inverse"):
                self.array(key + "/" + prop, np.asarray(getattr(obj, prop), dtype=np.float64))
            self.animation(key + "/animation", obj)
            if obj.type == "MESH":
                self.mesh(obj.data)
                if obj.vertex_groups:
                    self.array(
                        key + "/vertex_group_weights",
                        np.asarray(
                            [
                                (vertex.index, group.group, group.weight)
                                for vertex in obj.data.vertices
                                for group in vertex.groups
                            ],
                            dtype=np.float64,
                        ),
                    )
            elif obj.type in {"CURVE", "FONT", "SURFACE"}:
                self.curve(obj.data)
            elif obj.data:
                self.records[key + "/data"] = settings(obj.data)
                self.animation(key + "/data_animation", obj.data)
            if obj.type == "LIGHT":
                self.nodes(key + "/light_nodes", obj.data.node_tree)
                self.counts["light_energy_W"] += obj.data.energy
        for material in bpy.data.materials:
            key = "material/" + material.name
            self.records[key] = dict(settings=settings(material), properties=plain(dict(material.items())))
            self.nodes(key + "/nodes", material.node_tree)
            self.animation(key + "/animation", material)
        for shape in bpy.data.shape_keys:
            self.shape(shape)
        for mesh in bpy.data.meshes:
            self.mesh(mesh)
        for curve in bpy.data.curves:
            self.curve(curve)
        for collection in bpy.data.collections:
            self.records["collection/" + collection.name] = dict(
                settings=settings(collection),
                objects=sorted(obj.name for obj in collection.objects),
                children=sorted(child.name for child in collection.children),
            )
        for action in bpy.data.actions:
            if action.name not in self.seen_actions:
                self.animation("unbound_action/" + action.name, action)
        for world in bpy.data.worlds:
            key = "world/" + world.name
            self.records[key] = settings(world)
            self.nodes(key + "/nodes", world.node_tree)
            self.animation(key + "/animation", world)
        for image in bpy.data.images:
            self.records["image/" + image.name] = dict(
                settings=settings(image),
                packed_sha256=hashlib.sha256(image.packed_file.data).hexdigest() if image.packed_file else None,
            )
        print("CAMERA_DELTA_SNAPSHOT", path.name, dict(self.counts), len(self.arrays), flush=True)


def compare(original: Snapshot, final: Snapshot) -> dict:
    """Compare exact fields and separately identify tiny matrix-only roundoff [m]."""
    missing_records = sorted(original.records.keys() ^ final.records.keys())
    changed_records = [
        key
        for key in original.records.keys() & final.records.keys()
        if json.dumps(original.records[key], sort_keys=True) != json.dumps(final.records[key], sort_keys=True)
    ]
    missing_arrays = sorted(original.arrays.keys() ^ final.arrays.keys())
    changed_arrays, roundoff = [], []
    for key in original.arrays.keys() & final.arrays.keys():
        a, b = original.arrays[key], final.arrays[key]
        if a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a.view(np.uint8), b.view(np.uint8)):
            continue
        error = float(np.max(abs(a.astype(float) - b.astype(float)), initial=0)) if a.shape == b.shape else None
        row = dict(key=key, old_shape=list(a.shape), new_shape=list(b.shape), maximum_absolute_difference=error)
        matrix = key.startswith("object/") and "/matrix_" in key
        (roundoff if matrix and error is not None and error <= MATRIX_TOLERANCE else changed_arrays).append(row)
    camera_unexpected = []
    if original.cameras.keys() != final.cameras.keys():
        camera_unexpected.append("review_camera_names")
    for name in original.cameras.keys() & final.cameras.keys():
        before, after = original.cameras[name], final.cameras[name]
        if before.get("parent_inverse") != after.get("parent_inverse"):
            camera_unexpected.append(name + "/parent_inverse")
        object_before, object_after = dict(before["object"]), dict(after["object"])
        allowed_pose = {
            "location",
            "rotation_euler",
            "rotation_quaternion",
            "rotation_axis_angle",
            "matrix_world",
            "matrix_local",
            "matrix_basis",
        }
        for record in (object_before, object_after):
            record["settings"] = {key: value for key, value in record["settings"].items() if key not in allowed_pose}
        if object_before != object_after:
            camera_unexpected.append(name + "/non_pose_settings")
        allowed_optics = {"lens", "angle", "angle_x", "angle_y"}
        optics_before = {key: value for key, value in before["camera"].items() if key not in allowed_optics}
        optics_after = {key: value for key, value in after["camera"].items() if key not in allowed_optics}
        if optics_before != optics_after:
            camera_unexpected.append(name + "/non_lens_settings")
    exact = not (missing_records or changed_records or missing_arrays or changed_arrays or roundoff)
    return dict(
        strict_non_camera_equality=exact,
        non_camera_changes=sorted(changed_records),
        missing_records=missing_records,
        missing_arrays=missing_arrays,
        changed_arrays=changed_arrays,
        matrix_roundoff_only=roundoff,
        unexpected_review_camera_changes=camera_unexpected,
        existing_matrix_tolerance=MATRIX_TOLERANCE,
        eligible_to_inherit_geometry_checks=not (
            missing_records or changed_records or missing_arrays or changed_arrays or camera_unexpected
        ),
        checked_record_count=len(original.records),
        checked_array_count=len(original.arrays),
        array_elements=sum(array.size for array in original.arrays.values()),
        original_counts=dict(original.counts),
        final_counts=dict(final.counts),
        camera_changes={
            name: dict(before=original.cameras[name], after=final.cameras[name]) for name in original.cameras
        },
        category_signatures=dict(original=signatures(original), final=signatures(final)),
    )


def signatures(snapshot: Snapshot) -> dict:
    """Hash compared fields by category, preserving native numeric bytes exactly."""
    hashes, counts = {}, {}
    for kind, values in (("record", snapshot.records), ("array", snapshot.arrays)):
        for key in sorted(values):
            category = "animation" if "/animation" in key or key.startswith("unbound_action/") else key.split("/")[0]
            hasher = hashes.setdefault(category, hashlib.sha256())
            counts.setdefault(category, Counter())[kind + "s"] += 1
            hasher.update(json.dumps([kind, key], ensure_ascii=False).encode())
            value = values[key]
            if kind == "array":
                hasher.update(json.dumps([str(value.dtype), list(value.shape)]).encode())
                hasher.update(value.tobytes())
            else:
                hasher.update(json.dumps(value, ensure_ascii=False, sort_keys=True).encode())
    return {category: dict(sha256=hasher.hexdigest(), **counts[category]) for category, hasher in hashes.items()}


def main() -> None:
    """Compare archived and final saved natives; write a separate immutable report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, default=BASE / "UR15_JB_OP030_split_v06.blend")
    parser.add_argument("--final", type=Path, required=True)
    parser.add_argument("--allowed_camera", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline_only", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    if args.output.exists():
        raise FileExistsError(args.output)
    original_sha = digest(args.original)
    if original_sha != OLD_SHA:
        raise ValueError("Original native is not the archived checked 8674 candidate")
    original = Snapshot(args.original, set(args.allowed_camera))
    if args.baseline_only:
        result = dict(
            baseline_only=True,
            counts=dict(original.counts),
            records=len(original.records),
            arrays=len(original.arrays),
            no_final_comparison=True,
        )
    else:
        final = Snapshot(args.final, set(args.allowed_camera))
        result = compare(original, final)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        original=str(args.original.resolve()),
        original_sha256=original_sha,
        final=str(args.final.resolve()),
        final_sha256=digest(args.final),
        allowed_review_cameras=args.allowed_camera,
        archive_manifest=str(BASE / "manifest.json"),
        archive_manifest_sha256=digest(BASE / "manifest.json"),
        source_sha256=digest(Path(__file__)),
        result=result,
        scope="Saved Blender data equivalence only. Original raw geometry evidence retains its native SHA. "
        "No new force, physical validity, or collision verdict.",
        formal_physical_validity_verdict=None,
    )
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if not args.baseline_only and not result["eligible_to_inherit_geometry_checks"]:
        raise SystemExit("CAMERA_DELTA_HAS_UNEXPECTED_CHANGES")
    print("CAMERA_DELTA_COMPLETE", args.output, flush=True)


if __name__ == "__main__":
    main()
