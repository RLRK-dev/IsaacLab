# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Compare axial exit projections with unchanged trial hand translations [m]."""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / "hvjb-inner-installed-access-v01-20260921"
sys.path.insert(0, str(PREVIOUS))
import probe_access as A  # noqa: E402

OUTPUT = ROOT / "output"
CONFIG = {
    "status": "auxiliary_projection_comparison_not_wire_routing_or_acceptance",
    "central_source_section_z_m": -0.0339 + 5e-7,
    "section_numeric_offset_m": 5e-7,
    "projected_interior_inset_m": 1e-9,
    "open_each_m": 0.004,
    "lift_m": 0.050,
    "comparison_open_each_m": 0.002,
    "projection": "source X/Y equals product-relative X/Z; axial coordinate is discarded",
    "central_region": "One convex envelope covering both central openings, not individual MQS hole dimensions.",
    "wire_centerline_or_diameter_selected": False,
}
DRAWING = A.G.REF / "references/hvjb_photo_inventory_20260915/te_2103245_drawing.pdf"
INSTRUCTION = A.G.REF / "references/connector_correction_20260915/te_408_32095_instruction.pdf"
PINS = {
    DRAWING: "23aff5f20acb75d87a63bf3a1aa0c076a8ab43b30c83914cfc8e5c9b41788ffa",
    INSTRUCTION: "cd13cd856b679e2683f7672f079bd4c99ff87ac2e361d3da73700e12c12fa63d",
}


def hull_loop(points):
    xy = np.unique(np.asarray(points)[:, :2], axis=0)
    return xy[ConvexHull(xy).vertices]


def exit_regions(housing):
    power = A.T.cavity_loops(housing)
    power.sort(key=lambda loop: loop[:, 0].mean())
    plane = CONFIG["central_source_section_z_m"]
    lines = trimesh.intersections.mesh_plane(housing, [0, 0, 1], [0, 0, plane])
    loops = trimesh.load_path(lines).discrete
    central = [loop for loop in loops if abs(loop[:, 0]).max() < 0.002 and abs(loop[:, 1]).max() < 0.0032]
    assert len(central) == 1, len(central)
    result = []
    for name, loop in zip(("POWER_LEFT", "POWER_RIGHT", "HVIL_PAIR_ENVELOPE"), [*power, central[0]], strict=True):
        outline = hull_loop(loop)
        xyz = np.column_stack((outline, np.zeros(len(outline))))
        result.append(
            {
                "id": name,
                "source_section_z_m": float(loop[0, 2]),
                "source_section_loop_m": loop.tolist(),
                "projection_polygon_m": outline.tolist(),
                "projection_bounds_m": [outline.min(0).tolist(), outline.max(0).tolist()],
                "projection_area_m2": A.G.polygon_area(xyz),
                "is_wire_shape": False,
            }
        )
    return result


def projected_parts(parts, origin):
    result = []
    for piece in parts:
        xy = (piece["mesh"].vertices - origin)[:, [0, 2]]
        hull = ConvexHull(xy)
        result.append(
            {
                "name": piece["name"],
                "kind": piece["kind"],
                "outline": xy[hull.vertices],
                "normals": np.column_stack((hull.equations[:, :2], np.zeros(len(hull.equations)))),
                "limits": -hull.equations[:, 2] - CONFIG["projected_interior_inset_m"],
            }
        )
    return result


def overlaps(regions, parts, origin):
    projected = projected_parts(parts, origin)
    result = []
    for region in regions:
        loop = np.asarray(region["projection_polygon_m"])
        polygon = np.column_stack((loop, np.zeros(len(loop))))
        hits = []
        for part in projected:
            clipped = A.G.clip_polygon(polygon, part["normals"], part["limits"])
            area = A.G.polygon_area(clipped)
            if area > A.G.CONFIG["clipped_area_reporting_epsilon_m2"]:
                hits.append({"part": part["name"], "projected_overlap_m2": area})
        result.append({"exit_region": region["id"], "positive_parts": hits, "overlap_observed": bool(hits)})
    return result


def read_inputs():
    for path, expected in PINS.items():
        assert A.P.sha(path) == expected, path
    old = json.loads((PREVIOUS / "output/installed_access_observations.json").read_text())
    assert A.P.sha(PREVIOUS / "probe_access.py") == old["script_sha256"]
    assert A.P.sha(A.P.DATA / "product_manifest.json") == old["input_manifest_sha256"]
    product, _ = A.P.load_product()
    inners, _, settings, _ = A.G.load_sources()
    pge_path = A.P.DATA / "hvjb_pge_finger_v01_meshes.json.gz"
    assert A.P.sha(pge_path) == old["pge_sha256"]
    return product, inners, settings, json.loads(gzip.decompress(pge_path.read_bytes()))


def comparison_states(parts):
    opened4 = A.pose(parts, opening=CONFIG["open_each_m"])
    opened2 = A.pose(parts, opening=CONFIG["comparison_open_each_m"])
    return {
        "closed": parts,
        "open_0_to_4": A.translation_sweeps(parts, opened4),
        "lift_0_to_50_after_open_4": A.translation_sweeps(
            opened4, A.pose(parts, opening=CONFIG["open_each_m"], lift=CONFIG["lift_m"])
        ),
        "lift_0_to_50_after_open_2": A.translation_sweeps(
            opened2, A.pose(parts, opening=CONFIG["comparison_open_each_m"], lift=CONFIG["lift_m"])
        ),
    }


def main():
    assert not (OUTPUT / "exit_projection_observations.json").exists()
    product, inners, settings, pge = read_inputs()
    rows = []
    for aperture in settings["apertures"]:
        housing = A.G.mesh(inners[aperture["part_number"]])
        regions = exit_regions(housing)
        parts, mapping = A.build_hand(inners[aperture["part_number"]], product[aperture["id"]], pge)
        origin = np.asarray(mapping["inner_origin_world_m"])
        comparisons = {name: overlaps(regions, state, origin) for name, state in comparison_states(parts).items()}
        rows.append(
            {
                "id": aperture["id"],
                "part_number": aperture["part_number"],
                "regions": regions,
                "mapping": mapping,
                "comparisons": comparisons,
            }
        )
        print(
            aperture["id"],
            {key: [r["exit_region"] for r in value if r["overlap_observed"]] for key, value in comparisons.items()},
            flush=True,
        )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result = {
        "config": CONFIG,
        "bays": rows,
        "sources": [{"path": str(p.relative_to(ROOT.parents[1])), "sha256": h} for p, h in PINS.items()],
        "prior_observations_sha256": A.P.sha(PREVIOUS / "output/installed_access_observations.json"),
        "prior_geometry_code_sha256": A.P.sha(PREVIOUS / "probe_access.py"),
        "source_cad_sha256": A.G.sha(A.G.INNER),
        "script_sha256": A.P.sha(Path(__file__)),
        "numerical_checks": A.numerical_checks(),
        "physical_verdict": None,
        "interpretation": [
            "Projected footprints are virtual axial channels, not actual fitted wires or selected wire diameters.",
            "Positive projected overlap is not necessarily a three-dimensional collision.",
            "Zero projected overlap excludes only the defined axial footprint from this hand comparison.",
            "Curved wires, barrels, bundling, HVIL loops, housing retention and actual assembly pose remain open.",
            "The central footprint assigns no individual HVIL terminal, polarity or electrical continuity.",
        ],
    }
    (OUTPUT / "exit_projection_observations.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("EXIT_PROJECTION_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
