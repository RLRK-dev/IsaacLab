# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Check authored display data; do not assess robot or assembly feasibility."""

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan_path = ROOT / "data/concept_v03.json"
    plan = json.loads(plan_path.read_text())
    bank_path = ROOT / "data" / plan["motion"]
    assert sha(bank_path) == plan["motion_sha256"]
    source = json.loads((ROOT / "inputs/line_process_plan.json").read_text())
    task_ids = {r["id"] for r in source["cards"]}
    assert task_ids == {task for row in plan["scenes"] for task in row.get("tasks", [])}
    assert len(task_ids) == 20
    assert len({r["operation"] for r in source["cards"]}) == 12
    with np.load(bank_path, allow_pickle=False) as bank:
        times, matrices, names = bank["time_s"], bank["matrices"], bank["object_names"].tolist()
        assert matrices.shape == (1785, 304, 4, 4)
        assert np.isfinite(matrices).all() and np.isfinite(bank["camera"]).all()
        assert np.array_equal(times, np.arange(1785) / 15)
        pallet = matrices[:, names.index("pallet"), :3, 3]
        pallet_z_span = float(np.ptp(pallet[:, 2]))
        # Interpolation of equal endpoints can differ by two float64 ULPs.
        rounding_bound = float(2 * np.spacing(0.8))
        assert pallet_z_span <= rounding_bound
        cases = [i for i, name in enumerate(names) if name == "case"]
        assert len(cases) == 8
        return_error = float(np.max(np.abs(matrices[0, cases] - matrices[-1, cases])))
        assert return_error == 0
        initial_pallet, final_pallet = pallet[0], pallet[-1]
        assert np.array_equal(initial_pallet, final_pallet)
        assist = matrices[times >= 44, names.index("AB補助_palm")]
        assist_delta = float(np.max(np.abs(assist - assist[0])))
        assert assist_delta == 0
        rise_mask = (times >= 91.86) & (times < 93)
        z_main = matrices[rise_mask, names.index("C主_palm"), 2, 3]
        z_assist = matrices[rise_mask, names.index("C補助_palm"), 2, 3]
        rise_delta = float(np.max(np.abs((z_main - z_main[0]) - (z_assist - z_assist[0]))))
        rise_rounding_bound = float(4 * np.spacing(max(abs(z_main).max(), abs(z_assist).max())))
        assert rise_delta <= rise_rounding_bound
    for row in json.loads((ROOT / "inputs/original_sources.json").read_text()):
        assert sha(Path(row["path"])) == row["sha256"]
    with (ROOT / "data/scene_index.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["場面", "開始秒", "終了秒", "仕事ID", "作業場所", "内容", "表示の限界"])
        for row in plan["scenes"]:
            writer.writerow(
                [
                    row["id"],
                    row["start_s"],
                    row["stop_s"],
                    ",".join(row.get("tasks", [])),
                    row.get("place_ja", "全体"),
                    row.get("title_ja", "全体"),
                    row.get("hold_or_limit_ja", "概略表示"),
                ]
            )
    report = dict(
        evidence_basis="Saved display arrays and pinned files; no physical or mechanical verdict.",
        bank_sha256=sha(bank_path),
        plan_sha256=sha(plan_path),
        source_tasks=20,
        source_operations=12,
        storyboard_scenes=16,
        output_frames=1785,
        fps=15,
        duration_s=119,
        dynamic_objects=304,
        pallet_z_span_display_units=pallet_z_span,
        pallet_z_rounding_bound_float64=rounding_bound,
        case_return_max_matrix_difference=return_error,
        case_parts_compared=8,
        pallet_return_position_identical=True,
        AB_assist_after_S06_max_matrix_difference=assist_delta,
        paired_rise_max_displacement_difference=rise_delta,
        paired_rise_rounding_bound_float64=rise_rounding_bound,
        original_files_unchanged=9,
        static_task_scenes=plan["static_task_scenes"],
        formal_physical_validity_verdict=None,
    )
    (ROOT / "audit/display_checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"DISPLAY_CHECKS_COMPLETE tasks=20 scenes=16 frames=1785 pallet_z_span={pallet_z_span} case_return_error=0")


if __name__ == "__main__":
    main()
