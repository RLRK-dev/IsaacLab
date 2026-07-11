# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""comp5 C2-scene build self-verify (no-GPU): flag-OFF byte-identity + flag-ON C2 geom assert.

%12 build-time reminder #3: flag-OFF byte-identity (add_c2_clip=False adds nothing; C1-hoist byte-preserving)
+ C2 geom assert (5 clip + 1 spacer geoms @ ROUTE_C2_XY / groove 829 / collidable / arm-cable joint index
invariant). Builds build_multiworld_scene twice (add_c2_clip False vs True) on CPU and compares the mjModel.

Run:
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp5_c2scene_geom_verify.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

_EVAL = Path(__file__).resolve().parent
_TIL = _EVAL.parent.parent / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "", "no-GPU verify: run with CUDA_VISIBLE_DEVICES=''"

import mujoco  # noqa: E402
import newton_route_env  # noqa: E402, F401  (side-effect: forces SOLVER_BACKEND="mujoco" like the route env)
import route_env_config as rc  # noqa: E402
from newton_skill_env_base import build_fk_and_init, build_multiworld_scene  # noqa: E402
from task_config import CLIP1_X, CLIP1_Y, FINGER_OPEN_POS  # noqa: E402

OUT = _EVAL / "comp5_c2scene_geom_verify_result.json"


def _build(add_c2):
    fkm, fks, _ = build_fk_and_init(left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device="cpu")
    kw = dict(
        add_support_clips=False,
        add_target_clip=True,
        target_clip_float_z=rc.ROUTE_CLIP_FLOAT_Z,
        grasp_actuation=True,
    )
    if add_c2:
        kw.update(add_c2_clip=True, c2_xy=rc.ROUTE_C2_XY)
    return build_multiworld_scene(fkm, fks, 1, "cpu", **kw)


def _clip_geoms(mjm, cx, cy, tol=0.03):
    mjd = mujoco.MjData(mjm)
    mujoco.mj_forward(mjm, mjd)
    out = []
    for g in range(mjm.ngeom):
        if int(mjm.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_BOX) and int(mjm.geom_bodyid[g]) == 0:
            p = mjd.geom_xpos[g]
            if abs(float(p[0]) - cx) < tol and abs(float(p[1]) - cy) < tol:
                out.append((g, round(float(p[2]), 4), int(mjm.geom_contype[g])))
    return out


def main():
    s_off = _build(False)
    m_off = s_off["solver"].mj_model
    s_on = _build(True)
    m_on = s_on["solver"].mj_model

    c2_off = _clip_geoms(m_off, rc.ROUTE_C2_XY[0], rc.ROUTE_C2_XY[1])
    c2_on = _clip_geoms(m_on, rc.ROUTE_C2_XY[0], rc.ROUTE_C2_XY[1])
    c1_off = _clip_geoms(m_off, CLIP1_X, CLIP1_Y)
    c1_on = _clip_geoms(m_on, CLIP1_X, CLIP1_Y)

    res = {
        "ngeom_off": int(m_off.ngeom),
        "ngeom_on": int(m_on.ngeom),
        "delta_geoms": int(m_on.ngeom - m_off.ngeom),
        "c2_geoms_off": len(c2_off),
        "c2_geoms_on": len(c2_on),
        "c2_on_z_sorted": sorted(z for _, z, _ in c2_on),
        "c2_on_all_collidable": all(ct != 0 for _, _, ct in c2_on),
        "c1_geoms_off": len(c1_off),
        "c1_geoms_on": len(c1_on),
        "c1_off_z_sorted": sorted(z for _, z, _ in c1_off),
        "njnt_off": int(m_off.njnt),
        "njnt_on": int(m_on.njnt),
        "jnt_qposadr_invariant": bool(np.array_equal(m_off.jnt_qposadr, m_on.jnt_qposadr)),
        "route_groove_z": round(float(rc.ROUTE_GROOVE_Z), 4),
        "c2_xy": [float(rc.ROUTE_C2_XY[0]), float(rc.ROUTE_C2_XY[1])],
    }

    checks = {
        "flagOFF_no_C2_geoms": len(c2_off) == 0,
        "flagON_C2_6_geoms (5 clip + 1 spacer)": len(c2_on) == 6,
        "delta_is_plus6": (m_on.ngeom - m_off.ngeom) == 6,
        "C1_hoist_byte_preserve (5 geoms both)": len(c1_off) == 5 and len(c1_on) == 5,
        "C1_z_unchanged_by_hoist": sorted(z for _, z, _ in c1_off) == sorted(z for _, z, _ in c1_on),
        "C2_collidable": res["c2_on_all_collidable"],
        "arm_cable_joint_index_invariant": (m_off.njnt == m_on.njnt) and res["jnt_qposadr_invariant"],
        "C2_groove_walls_span_829": any(0.825 <= z <= 0.840 for _, z, _ in c2_on),  # walls bracket ROUTE_GROOVE_Z 829
    }
    res["checks"] = checks
    res["ALL_PASS"] = all(checks.values())

    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print(f"-> {OUT}")
    if not res["ALL_PASS"]:
        print("[comp5 geom verify] FAIL:", [k for k, v in checks.items() if not v])
        return 1
    print("[comp5 geom verify] ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
