# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reproduce the exact-zero mj_geomDistance artifact on the KINONLY cell.

⛔ THE MEASURED FACT (first isolated 2026-08-09 on mujoco 3.10.0, driving the fix committed as
"Re-measure exact-zero distances at a jittered pose"): a mesh pair 61.590 mm apart returns
EXACTLY 0.0 from mj_geomDistance at every cutoff when the pose is perturbed by ONE ULP -- the
perturbation being nothing more than computing ``0.95*q + 0.05*q`` in place of ``q`` (max qpos
delta 8.9e-16 rad, geom_xpos delta below 1e-12) -- and returns +61.590 again at the original
bits.  Deterministic and reversible, so the 0.0 is a narrowphase failure sentinel wearing a
contact's clothes.  Before the fix it printed as "+0.0" clearance in 23 of 25 shakedown rows,
and the fixed run re-queried 393,301 such readings of which 99.73% moved off zero under jitter.

Needs `_gen/kinonly_solutions.json` from a `kinonly_step_solve.py` run (the banked winner joint
vectors are the reproduction coordinates).  Read-only kinematics; never steps.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kinonly_step_solve as K  # noqa: E402  (installs its audit hook and C-2 env overrides)
import mujoco  # noqa: E402


def main() -> int:
    bank = json.loads((HERE / "_gen" / "kinonly_solutions.json").read_text())
    row = next(r for r in bank["rows"] if "q_L" in r)
    m, _ = K.build_cell()
    d = mujoco.MjData(m)
    grp = K.geom_groups(m)
    qadr = {t: [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")]
                for j in K.J6] for t in ("L", "R")}

    def place(qs: dict) -> None:
        for t in ("L", "R"):
            for k, a in enumerate(qadr[t]):
                d.qpos[a] = qs[t][k]
        mujoco.mj_kinematics(m, d)

    w = {"L": np.array(row["q_L"]), "R": np.array(row["q_R"])}
    wi = {t: 0.95 * w[t] + 0.05 * w[t] for t in ("L", "R")}   # same pose, one ulp of arithmetic
    print(f"probe row: STEP {row['step']} ({row['candidate']}); "
          f"max |q - (0.95q+0.05q)| = {max(float(np.max(np.abs(wi[t] - w[t]))) for t in ('L', 'R')):.3e} rad")

    flips = []
    for label, qs in (("original bits", w), ("ulp-shifted", wi), ("original again", w)):
        place(qs)
        out = []
        for gl, A, B in (("arm-arm", grp["L"], grp["R"]),
                         ("L-env", grp["L"], grp["env"]),
                         ("R-env", grp["R"], grp["env"])):
            best, bwho = None, "-"
            for a in A:
                for b in B:
                    # ⚠ Raw mj_geomDistance ON PURPOSE -- this probe demonstrates the artifact
                    # the instrument's closest() now guards against, so it must not use closest().
                    v = mujoco.mj_geomDistance(m, d, a, b, 0.5, None)
                    if v < 0.5 and (best is None or v < best):
                        best, bwho = v, f"{a}<->{b}"
            out.append(f"{gl} {'None' if best is None else f'{best * 1000:+.4f}mm'} ({bwho})")
            if best == 0.0:
                flips.append((label, gl, bwho))
        print(f"  {label:>14}: " + " | ".join(out))
    print(f"exact-zero minima seen: {len(flips)} -> {flips if flips else 'none at these poses'}")
    print("interpretation: an exact 0.0 that appears only on the ulp-shifted placement is the "
          "narrowphase failure sentinel; kinonly_step_solve.closest() re-queries such readings "
          "at 1e-12/1e-11 rad jitter and keeps a 0.0 only if it survives both.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
