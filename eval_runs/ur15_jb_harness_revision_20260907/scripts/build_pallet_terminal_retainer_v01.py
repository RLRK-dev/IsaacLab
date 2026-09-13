# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build a static rest/cap fixture comparison around the existing terminal hand [m]."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import build_hand_fingertip_concepts_v01 as base
import build_hand_terminal_concepts_v01 as terminal
import numpy as np
import trimesh


def _saddle(config, target_config, upper):
    f = config["fixture"]
    center_z = target_config["seat_z_m"] + target_config["raw_barrel_axis_above_seat_m"]
    x = np.linspace(-f["saddle_width_m"] / 2, f["saddle_width_m"] / 2, 81)
    arc = np.sqrt(np.maximum(0, f["saddle_radius_m"] ** 2 - x**2))
    surface_z = center_z + (arc if upper else -arc)
    back = f["upper_back_z_m"] if upper else f["lower_back_z_m"]
    vertices = [(a, y, z) for y in f["saddle_y_range_m"] for a, z in zip(x, surface_z, strict=True)]
    vertices.extend((a, y, back) for y in f["saddle_y_range_m"] for a in x)
    count, faces = len(x), []
    for i in range(count - 1):
        for start in (0, 2 * count):
            a = start + i
            faces.extend(((a, a + 1, a + count + 1), (a, a + count + 1, a + count)))
        for start in (0, count):
            a = start + i
            faces.extend(((a, a + 1, a + 2 * count + 1), (a, a + 2 * count + 1, a + 2 * count)))
    for a in (0, count - 1):
        faces.extend(((a, a + count, a + 3 * count), (a, a + 3 * count, a + 2 * count)))
    mesh = base._mesh(vertices, faces, "pad")
    if not mesh.is_watertight:
        raise ValueError("Saddle comparison mesh is not closed")
    mesh.visual.vertex_colors = [69, 105, 93, 255]
    return mesh


def _fixtures(config, target_config, with_cap):
    f = config["fixture"]
    fixed = {
        "local_base": base._box(f["base_dimensions_m"], f["base_center_m"], "hardware"),
        "coupon_support": base._box(f["coupon_support_dimensions_m"], f["coupon_support_center_m"], "hardware"),
        "lower_saddle": _saddle(config, target_config, False),
        "saddle_support": base._box(f["saddle_support_dimensions_m"], f["saddle_support_center_m"], "hardware"),
    }
    moving = {}
    if with_cap:
        moving = {
            "upper_saddle": _saddle(config, target_config, True),
            "swing_beam": base._box(f["beam_dimensions_m"], f["beam_center_m"], "support"),
        }
        for i, center in enumerate(f["hinge_post_centers_m"]):
            fixed[f"hinge_post_{i}"] = base._box(f["hinge_post_dimensions_m"], center, "hardware")
        hinge = trimesh.creation.cylinder(radius=f["hinge_radius_m"], height=f["hinge_length_m"], sections=48)
        hinge.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        hinge.apply_translation(f["hinge_center_m"])
        hinge.visual.vertex_colors = base.COLORS["hardware"]
        fixed["hinge_pin"] = hinge
    return fixed, moving


def _candidate(source, config, target_config, with_cap):
    candidate = copy.deepcopy(source)
    fixed, moving = _fixtures(config, target_config, with_cap)
    for name, mesh in {**fixed, **moving}.items():
        candidate["objects"][name] = base._serialize(mesh, "fixture")
    if with_cap:
        f = config["fixture"]
        reserved = base._box(f["lock_reserved_dimensions_m"], f["lock_reserved_center_m"], "guide")
        reserved.visual.vertex_colors = [240, 159, 38, 65]
        candidate["objects"]["lock_mechanism_reserved_only"] = base._serialize(reserved, "guide")
    candidate["states"] = {}
    identity = np.eye(4).tolist()
    for name, definition in config["states"].items():
        state = copy.deepcopy(source["states"][definition["source_hand_state"]])
        state["hidden_objects"] = [
            n
            for n, obj in source["objects"].items()
            if definition["hide_hand"] and obj["category"] in ("hardware", "insert")
        ]
        state["cap_angle_rad"] = config["fixture"]["open_angle_rad"] if definition["cap_open"] else 0.0
        state["transforms"].update({n: identity for n in fixed})
        rotate = trimesh.transformations.rotation_matrix(
            state["cap_angle_rad"], [1, 0, 0], config["fixture"]["hinge_center_m"]
        )
        state["transforms"].update({n: rotate.tolist() for n in moving})
        if with_cap:
            state["transforms"]["lock_mechanism_reserved_only"] = identity
        candidate["states"][name] = state
    candidate["note"] = "Fixed target in five discrete poses; no force, locking or transport simulation."
    return candidate


def _geometry_observations(candidate, target_config):
    rows = {}
    seat = target_config["target"]["seat_z_m"]
    tool = target_config["illustrative_surroundings"]
    low, high = np.array(tool["tool_z_above_seat_range_m"]) + seat
    for state_name, state in candidate["states"].items():
        bounds, radial_bounds = {}, []
        for name, obj in candidate["objects"].items():
            if obj["category"] != "fixture":
                continue
            matrix = np.asarray(state["transforms"][name])
            world = np.asarray(obj["vertices"]) @ matrix[:3, :3].T + matrix[:3, 3]
            bounds[name] = [world.min(axis=0).tolist(), world.max(axis=0).tolist()]
            triangles = world[np.asarray(obj["faces"])]
            selected = triangles[(triangles[:, :, 2].min(axis=1) <= high) & (triangles[:, :, 2].max(axis=1) >= low)]
            if len(selected):
                radial_bounds.append((terminal._projected_radius_min(selected) - tool["tool_radius_m"], name))
        rows[state_name] = {
            "fixture_bounds_m": bounds,
            "tool_radius_projected_lower_bound_m": min(radial_bounds)[0] if radial_bounds else None,
            "limiting_fixture": min(radial_bounds)[1] if radial_bounds else None,
            "hidden_hand_meshes": state["hidden_objects"],
        }
    return rows


def main() -> None:
    """Build a fresh review directory from a hash-checked static source."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "source_payload", "output_directory"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if base._digest(args.source_payload) != config["input_payload_sha256"]:
        raise ValueError("Prior terminal payload SHA mismatch")
    template_path = Path(__file__).with_name("pallet_terminal_retainer_viewer_v01.html")
    inputs = [
        args.config,
        args.source_payload,
        Path(__file__),
        Path(base.__file__),
        Path(terminal.__file__),
        template_path,
    ]
    before = {str(p): base._digest(p) for p in inputs}
    source = json.loads(args.source_payload.read_text())
    candidates = {
        name: _candidate(source["candidates"]["EDGE"], config, source["config"]["target"], has_cap)
        for name, has_cap in (("REST", False), ("CAP", True))
    }
    payload = {"config": config, "reference_config": source["config"], "candidates": candidates}
    args.output_directory.mkdir(parents=True, exist_ok=False)
    packed = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    (args.output_directory / "pallet_terminal_retainer_meshes_v01.json").write_text(packed + "\n")
    (args.output_directory / "端末保持治具3D比較_v01.html").write_text(
        template_path.read_text().replace("__MESH_PAYLOAD__", packed.replace("<", "\\u003c"))
    )
    exports = []
    for name, candidate in candidates.items():
        # The standalone GLB shows the closed comparison pose; source helpers use the key 'near'.
        export_candidate = copy.deepcopy(candidate)
        export_candidate["states"]["near"] = candidate["states"]["clamp"]
        exports.append(base._export_glb(export_candidate, args.output_directory / f"terminal_retainer_{name}_v01.glb"))
    if before != {str(p): base._digest(p) for p in inputs}:
        raise RuntimeError("A read-only source changed during the build")
    report = {
        "scope": "static occupancy and input preservation observations only",
        "inputs_unchanged": True,
        "source_sha256": before,
        "reused_hand": "EDGE; original vertices/faces and recorded hand transforms copied unchanged",
        "target_geometry_copied_unchanged": all(
            candidate["objects"]["reference_lug_6R6_uncrimped"]
            == source["candidates"]["EDGE"]["objects"]["reference_lug_6R6_uncrimped"]
            for candidate in candidates.values()
        ),
        "saddle_nominal_radial_gap_m": config["fixture"]["saddle_radius_m"]
        - source["config"]["target"]["sleeve_outer_radius_m"],
        "static_poses": {
            name: _geometry_observations(candidate, source["config"]) for name, candidate in candidates.items()
        },
        "measurement_basis": "triangle XY projection within tool Z band is a conservative bound, not exact clearance",
        "exports": exports,
        "not_evaluated": config["unresolved"],
        "physical_acceptance_verdict": None,
    }
    (args.output_directory / "pallet_terminal_retainer_geometry_v01.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({"exports": exports, "radial_display_gap_m": report["saddle_nominal_radial_gap_m"]}, indent=2))
    print("PALLET_TERMINAL_RETAINER_STATIC_DONE", flush=True)


if __name__ == "__main__":
    main()
