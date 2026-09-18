# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Compare catalog fastener conditions using saved observations; do not open or modify geometry."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/hvjb_header_screw_options_v01.json"
OUTPUT = ROOT / "audit/hvjb_header_screw_options_v01.json"


def _sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def _conditional_position(model, screw, example, length):
    """Compute conditional axial positions [m], without thread/contact assessment."""
    plane = screw["nearest_parallel_plane_local_y_m"] + model["model_translation_m"][1]
    outer, inner = screw["front_wall_interval_world_y_m"]
    head_back = plane - example["separate_washer_in_under_head_length_m"]
    tip = head_back + length
    return {
        "feature_id": model["feature_id"],
        "source_screw": screw["name"],
        "source_axis_world_xz_m": screw["axis_world_xz_m"],
        "catalog_family": example["id"],
        "nominal_length_m": length,
        "saved_support_plane_world_y_m": plane,
        "saved_wall_interval_world_y_m": [outer, inner],
        "saved_plane_to_wall_outer_m": outer - plane,
        "conditional_head_back_world_y_m": head_back,
        "conditional_head_outer_world_y_m": head_back - example["head_height_m"],
        "conditional_tip_world_y_m": tip,
        "conditional_tip_minus_wall_outer_m": tip - outer,
        "conditional_tip_minus_wall_inner_m": tip - inner,
        "effective_thread_engagement_m": None,
        "physical_acceptance_verdict": None,
    }


def _catalog_differences(example, conditions):
    """Report catalog nominal differences [m, N·m], not manufacturing clearance."""
    torque = example["published_max_torque_nm"]
    lower, upper = conditions["torque_range_nm"]
    return {
        "catalog_family": example["id"],
        "nominal_retention_diameter_minus_te_min_m": (
            example["retention_diameter_m"] - conditions["minimum_retention_diameter_m"]
        ),
        "te_max_head_diameter_minus_catalog_nominal_m": (
            conditions["maximum_head_diameter_m"] - example["head_diameter_m"]
        ),
        "te_max_outside_height_minus_catalog_nominal_m": (
            conditions["maximum_height_outside_head_diameter_m"] - example["outside_height_m"]
        ),
        "catalog_max_torque_nm": torque,
        "catalog_max_minus_te_lower_nm": None if torque is None else torque - lower,
        "catalog_max_minus_te_upper_nm": None if torque is None else torque - upper,
        "manufacturing_limits_verified": False,
        "selected": False,
    }


def main():
    """Save comparisons and verify all protected input identities."""
    assert not OUTPUT.exists(), f"Refusing to overwrite {OUTPUT}"
    spec = json.loads(INPUT.read_text())
    prior_path = ROOT / spec["previous_observation"]
    assert _sha(prior_path) == spec["previous_observation_sha256"]
    prior = json.loads(prior_path.read_text())
    expected = dict(prior["input_sha256_after"])
    expected[spec["previous_observation"]] = spec["previous_observation_sha256"]
    expected[str(INPUT.relative_to(ROOT))] = _sha(INPUT)
    expected.update({source["path"]: source["sha256"] for source in spec["sources"]})
    before = {relative: _sha(ROOT / relative) for relative in expected}
    assert before == expected, "Protected input identity differs"
    assert prior["source_feature_count"] == 92
    assert sum(len(model["screws"]) for model in prior["models"]) == 14

    cases = [
        _conditional_position(model, screw, example, length)
        for model in prior["models"]
        for screw in model["screws"]
        for example in spec["catalog_examples"]
        for length in example["lengths_for_comparison_m"]
    ]
    summary = []
    for example in spec["catalog_examples"]:
        for length in example["lengths_for_comparison_m"]:
            rows = [r for r in cases if r["catalog_family"] == example["id"] and r["nominal_length_m"] == length]
            assert len(rows) == 14
            ranges = {}
            for key in ("conditional_tip_minus_wall_outer_m", "conditional_tip_minus_wall_inner_m"):
                values = [row[key] for row in rows]
                ranges[key] = [min(values), max(values)]
            summary.append({"catalog_family": example["id"], "nominal_length_m": length, "axes": len(rows), **ranges})

    after = {relative: _sha(ROOT / relative) for relative in expected}
    assert after == before
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": spec["scope_ja"],
        "conditional_calculation": spec["conditional_calculation"],
        "catalog_differences": [_catalog_differences(e, spec["te_conditions"]) for e in spec["catalog_examples"]],
        "summary": summary,
        "conditional_cases": cases,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "script_sha256": _sha(Path(__file__)),
        "mesh_queries_repeated": False,
        "scene_opened": False,
        "model_modified": False,
        "selected_fastener": None,
        "physical_acceptance_verdict": None,
    }
    with OUTPUT.open("x") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    assert json.loads(OUTPUT.read_text()) == result
    for row in summary:
        print("NOMINAL_STACK", json.dumps(row))
    print("HEADER_SCREW_OPTIONS_COMPLETE", len(cases), "cases;", len(after), "input hashes; JSON readback")


if __name__ == "__main__":
    main()
