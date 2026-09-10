# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Check constant M6 housing roll with independently indexed AF10 output [m, rad]."""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_c_cartesian_refill_v05 import trace
from op030_c_front_replay_v05 import MESH
from op030_c_refill_v05 import refill_phases
from op030_c_replay_v05 import aligned_pairs
from op030_definition import ROOT, pose
from op030_fk_fast import LIMITS, chain_for
from op030_split_c_v04 import digest
from op030_split_c_v05 import combined_row, source_tracks
from op030_split_c_v05_check import Context
from solve_op030_motion import R

HALF_TURN = pose(np.diag([-1.0, -1.0, 1.0]))


class FrontContext(Context):
    """Rebase source controls once for new supply positions and M6 phase [m, rad]."""

    def __init__(self, names):
        super().__init__(names, MESH)
        self.deltas = [pose(location=(0.45, 0.20, 0)), pose(location=(0.45, -0.20, 0))]

    def source_row(self, row):
        """Maintain exact supplied UID orientation through attachment and release [rad]."""
        result = dict(row)
        result["object_poses"] = row["object_poses"].copy()
        result["spindle_angles"] = row["spindle_angles"].copy()
        result["spindle_angles"][0] += np.pi
        owners = dict(zip(row["ledger_uids"], row["ledger_owner"], strict=True))
        for index, name in enumerate(self.names):
            if "feeder" not in str(name):
                continue
            arm = int("M14" in str(name))
            if name not in owners or owners[name] == 0:
                result["object_poses"][index] = self.deltas[arm] @ result["object_poses"][index]
            elif arm == 0:
                result["object_poses"][index] = result["object_poses"][index] @ HALF_TURN
        return result

    def query(self, row, joints=None):
        return super().query(self.source_row(row), joints)


def main():
    output = ROOT / "audit/op030_c_front_roll_v05.json"
    if output.exists():
        raise FileExistsError(output)
    data, _, tracks = source_tracks()
    context = FrontContext(data["object_names"])
    previous = [
        json.loads((ROOT / "audit" / name).read_text())
        for name in ("op030_c_near_branch_survey_v05.json", "op030_c_near_common_branch_v05.json")
    ]
    work = {
        2: np.asarray(previous[0]["returns"][0]["joints"][0]),
        1: np.asarray(previous[1]["records"][0]["records"][0]["joints"][0]),
    }
    results = []
    for number, order in ((2, (0, 1)), (1, (1, 0))):
        refill = refill_phases(tracks, number)
        goal = [p[3]["stop_frame"] for p in refill]
        row = combined_row(data, tracks, *goal)
        q = work[number].copy()
        records = []
        for arm in order:
            size = "M6" if arm == 0 else "M14"
            calibration = np.asarray(context.metadata["fixed_tools"]["OP030C_" + size]["flange_to_tcp"])
            chain = chain_for(tuple((row["poses"][0] @ R.yoke_base_pose("left" if arm == 0 else "right")).ravel()))
            begin = chain.forward(q[arm])[0] @ calibration
            end = context.deltas[arm] @ row["tools"][arm] @ calibration
            if arm == 0:
                end = end @ HALF_TURN
            result = trace(context, row, q, arm, [begin, end], half_turn_sign=1)
            result.update(arm=arm, size=size)
            records.append(result)
            print("C_FRONT_ROLL_RETURN", number, size, result["passed"], result["checked_states"], flush=True)
            if not result["passed"]:
                break
            q = np.asarray(result["joints"][-1])
        record = dict(number=number, returns=records)
        if len(records) == 2 and all(r["passed"] for r in records):
            pairs = aligned_pairs(goal, [p[-1]["stop_frame"] for p in refill])
            samples, failures = [], []
            for index, pair in enumerate(pairs):
                controls = combined_row(data, tracks, *pair)
                for arm, size in enumerate(("M6", "M14")):
                    calibration = np.asarray(context.metadata["fixed_tools"]["OP030C_" + size]["flange_to_tcp"])
                    tcp = context.deltas[arm] @ controls["tools"][arm] @ calibration
                    if arm == 0:
                        tcp = tcp @ HALF_TURN
                    chain = chain_for(
                        tuple((controls["poses"][0] @ R.yoke_base_pose("left" if arm == 0 else "right")).ravel())
                    )
                    value, residual = chain.solve_continuous(tcp @ np.linalg.inv(calibration), q[arm])
                    if residual > 1e-5 or abs(value - q[arm]).max() > 0.3 or np.any(abs(value) >= LIMITS):
                        failures.append(dict(index=index, arm=arm, residual=residual))
                        break
                    q[arm] = value
                if failures:
                    break
                hits, _ = context.query(controls, q)
                if hits:
                    failures.append(dict(index=index, pairs=hits))
                    break
                samples.append(q.copy())
            record.update(pickup_states=len(samples), pickup_failures=failures)
            print("C_FRONT_ROLL_PICKUP", number, len(samples), failures[:1], flush=True)
        results.append(record)
    output.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                source_sha256=digest(Path(__file__)),
                mesh_sha256=digest(MESH),
                records=results,
                additional_contact_exceptions=[],
                formal_physical_verdict=False,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
