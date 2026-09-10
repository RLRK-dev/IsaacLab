# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Inspect only the changed support-release and paired-ascent windows [m, rad, s]."""

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import LIMITS, chain_for
from op030_motion import SIDES
from op030_support_motion_v05 import support_sequence_v05
from op030_support_plan_v04 import PlanningContext as ContextV04
from op030_support_plan_v04 import digest
from solve_op030_motion import R

BANK = ROOT / "data/op030_split_a_motion_v04.npz"
MESH = ROOT / "data/op030_split_a_final_supported_v04_meshes.npz"


class PlanningContext(ContextV04):
    """Reuse the unchanged original-FK and simultaneous native mesh checker [m, rad, s]."""

    def __init__(self, mesh_file: Path = MESH):
        super().__init__(mesh_file)
        self.sequence = support_sequence_v05()


def bank_seed(bank: dict, old_author_time: float) -> np.ndarray:
    """Interpolate a nearby saved seed without modifying the bank [rad, s]."""
    return np.asarray(
        [
            [np.interp(old_author_time, bank["author_times"], bank["joints"][:, arm, joint]) for joint in range(6)]
            for arm in (0, 1)
        ]
    )


def solve_pair(context: PlanningContext, time: float, seed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Track both fixed Cartesian targets from the preceding accepted joints [rad, s]."""
    target = context.sequence.evaluate(time)
    result, errors = [], []
    for arm, side in enumerate(SIDES):
        base = target["root"] @ R.yoke_base_pose(side)
        q, error = chain_for(tuple(base.ravel())).solve_continuous(target["tools"][arm], seed[arm])
        result.append(q)
        errors.append(error)
    return np.asarray(result), np.asarray(errors)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("release", "ascent"), required=True)
    parser.add_argument("--mesh_file", type=Path, default=MESH)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.with_suffix(".npz").exists():
        raise FileExistsError(args.output)
    inputs = [
        BANK,
        args.mesh_file,
        args.mesh_file.with_suffix(".json"),
        Path(__file__),
        ROOT / "scripts/op030_support_motion_v05.py",
        ROOT / "scripts/op030_support_motion_v04.py",
        ROOT / "scripts/op030_split_ac_meshes.py",
    ]
    hashes = {str(path): digest(path) for path in inputs}
    with np.load(BANK) as saved:
        bank = {name: saved[name].copy() for name in ("author_times", "joints")}
    context = PlanningContext(args.mesh_file)
    results, arrays = [], {}
    for window in context.sequence.simultaneous_retreats:
        start = window["start_s"]
        stop = window["release_stop_s"] if args.stage == "release" else window["lift_stop_s"]
        times = np.unique(
            np.r_[np.linspace(start, stop, int(round((stop - start) * 60)) + 1), window["release_stop_s"]]
        )
        q = bank_seed(bank, window["old_start_s"])
        rows, failures, maximum_residual, maximum_jump = [], [], 0.0, 0.0
        for index, stamp in enumerate(times):
            solved, error = solve_pair(context, float(stamp), q)
            maximum_residual = max(maximum_residual, float(error.max()))
            maximum_jump = max(maximum_jump, float(abs(solved - q).max()))
            bad_ik = bool(error.max() > 1e-5 or np.any(abs(solved) > LIMITS + 1e-7) or abs(solved - q).max() > 0.2)
            score, pairs = context.query(float(stamp), solved)
            if bad_ik or score:
                failures.append(
                    dict(
                        index=index,
                        author_time_s=float(stamp),
                        ik_error=error.tolist(),
                        joint_step_rad=float(abs(solved - q).max()),
                        pairs=pairs,
                    )
                )
                if len(failures) >= 3:
                    break
            rows.append(solved.copy())
            q = solved
        arrays[f"window_{window['number']}_times"] = times[: len(rows)]
        arrays[f"window_{window['number']}_joints"] = np.asarray(rows)
        results.append(
            dict(
                window=window,
                sampled_states=len(rows),
                requested_states=len(times),
                maximum_residual=maximum_residual,
                maximum_joint_step_rad=maximum_jump,
                failures=failures,
                passed=not failures and len(rows) == len(times),
            )
        )
        print("A_V05_LOCAL", args.stage, window["number"], len(rows), len(failures), flush=True)
    np.savez_compressed(args.output.with_suffix(".npz"), **arrays)
    unchanged = hashes == {str(path): digest(path) for path in inputs}
    result = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        stage=args.stage,
        windows=results,
        source_inputs_sha256=hashes,
        inputs_unchanged=unchanged,
        passed=unchanged and all(row["passed"] for row in results),
        candidate_arrays=str(args.output.with_suffix(".npz")),
        candidate_arrays_sha256=digest(args.output.with_suffix(".npz")),
        additional_contact_exceptions=[],
        original_bank_modified=False,
        geometry_modified=False,
        scope="Local 60 Hz FK/native-mesh screen only; no force or formal physical-validity verdict",
    )
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
