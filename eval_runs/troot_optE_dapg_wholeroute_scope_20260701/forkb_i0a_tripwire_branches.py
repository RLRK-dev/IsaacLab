# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""fork-B I0-a tripwire identifiability -- the four D1 sec 4 branches, each asserted BOTH ways.

(i) CPU x wc=4 bare -> RAISE (the refusal leg) ; (ii) CPU x wc=1 -> passes ; (iii) opt-out=1 x CPU x wc=4 ->
passes (recorded-use diagnostics) ; (iv) use_mujoco_cpu=False x wc=4 -> the tripwire does NOT fire (the S8 path
is not blocked). Build-only (no stepping); CPU device; each branch isolated in a subprocess so env-var state
cannot leak between branches.

Run:
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/forkb_i0a_tripwire_branches.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
OUT = _EVAL / "forkb_i0a_tripwire_branches_result.json"

_CHILD = r"""
import os, sys
from pathlib import Path
_TIL = Path(r"{til}")
for _p in (str(_TIL), str(_TIL / "envs")):
    sys.path.insert(0, _p)
import newton_route_env  # noqa: F401  (SOLVER_BACKEND="mujoco")
import route_env_config as rc
from newton_skill_env_base import build_fk_and_init, build_multiworld_scene, make_solver
from task_config import FINGER_OPEN_POS
fkm, fks, _ = build_fk_and_init(left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device="cpu")
try:
    s = build_multiworld_scene(fkm, fks, {wc}, "cpu", add_support_clips=False, add_target_clip=True,
        target_clip_float_z=rc.ROUTE_CLIP_FLOAT_Z, add_c2_clip=True, c2_xy=rc.ROUTE_C2_XY,
        grasp_actuation=True, perclip_pin=True)
    print("BUILD_OK use_mujoco_cpu=", getattr(s["solver"], "use_mujoco_cpu", None))
    sys.exit(0)
except RuntimeError as e:
    if "single-world CPU template" in str(e):
        print("TRIPWIRE_RAISED")
        sys.exit(42)
    raise
"""


def _branch(name, wc, env_extra):
    til = str(_EVAL.parent.parent / "thread_isaac_lab")
    code = _CHILD.format(til=til, wc=wc)
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "NEWTON_DEVICE": "cpu", **env_extra}
    env.pop("THREAD_ALLOW_CPU_MULTIWORLD", None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=600)
    tail = (p.stdout or "").strip().splitlines()[-1] if p.stdout else ""
    return {"branch": name, "rc": p.returncode, "tail": tail[-120:]}


def main():
    # branch (iv) needs the warp path: monkeypatch via env? use_mujoco_cpu=False must come through make_solver --
    # build_multiworld_scene doesn't expose it, so branch (iv) tests make_solver DIRECTLY on the built model.
    results = []
    results.append({**_branch("i_cpu_wc4_bare", 4, {}), "expect": "rc=42 TRIPWIRE_RAISED"})
    results.append({**_branch("ii_cpu_wc1", 1, {}), "expect": "rc=0 BUILD_OK"})
    results.append(
        {
            **_branch("iii_optout_cpu_wc4", 4, {"THREAD_ALLOW_CPU_MULTIWORLD": "1"}),
            "expect": "rc=0 BUILD_OK (recorded-use diagnostics)",
        }
    )
    # (iv): direct make_solver with use_mujoco_cpu=False on a wc=4 model -- tripwire must not fire.
    til = str(_EVAL.parent.parent / "thread_isaac_lab")
    code_iv = rf"""
import os, sys
from pathlib import Path
_TIL = Path(r"{til}")
for _p in (str(_TIL), str(_TIL / "envs")):
    sys.path.insert(0, _p)
import newton_route_env  # noqa: F401
import route_env_config as rc
from newton_skill_env_base import build_fk_and_init, build_multiworld_scene, make_solver
from task_config import FINGER_OPEN_POS
import newton_skill_env_base as base
_orig = base.make_solver
calls = {{}}
def probe_make_solver(model, backend=base.SOLVER_BACKEND, use_mujoco_cpu=None, enable_cable_contacts=False):
    # force the S8 flag for THIS build; the tripwire must not raise on this path
    return _orig(model, backend=backend, use_mujoco_cpu=False, enable_cable_contacts=enable_cable_contacts)
base.make_solver = probe_make_solver
fkm, fks, _ = build_fk_and_init(left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device="cpu")
s = build_multiworld_scene(fkm, fks, 4, "cpu", add_support_clips=False, add_target_clip=True,
    target_clip_float_z=rc.ROUTE_CLIP_FLOAT_Z, add_c2_clip=True, c2_xy=rc.ROUTE_C2_XY,
    grasp_actuation=True, perclip_pin=True)
print("BUILD_OK_S8 use_mujoco_cpu=", getattr(s["solver"], "use_mujoco_cpu", None))
"""
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "NEWTON_DEVICE": "cpu"}
    env.pop("THREAD_ALLOW_CPU_MULTIWORLD", None)
    p = subprocess.run([sys.executable, "-c", code_iv], capture_output=True, text=True, env=env, timeout=600)
    results.append(
        {
            "branch": "iv_s8_wc4",
            "rc": p.returncode,
            "tail": (p.stdout or "").strip().splitlines()[-1][-120:] if p.stdout else "",
            "expect": "rc=0 BUILD_OK_S8 (tripwire silent on the warp path)",
        }
    )

    ok = (
        results[0]["rc"] == 42
        and "TRIPWIRE_RAISED" in results[0]["tail"]
        and results[1]["rc"] == 0
        and "BUILD_OK" in results[1]["tail"]
        and results[2]["rc"] == 0
        and "BUILD_OK" in results[2]["tail"]
        and results[3]["rc"] == 0
        and "BUILD_OK_S8" in results[3]["tail"]
    )
    out = {"branches": results, "ALL_PASS": ok}
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
