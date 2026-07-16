# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""I0-a positive controls (D1 sec 4:78): the two intentional multi-world probes still run under the tripwire.

Fresh executions of pin_multiworld_E_probe and pin_multiworld_E1v2_release_contrast AFTER the tripwire landed,
with their opt-out lines active. Outputs are REDIRECTED to *_postI0a.json (the banked artifacts are never
overwritten). PRE-DECLARED expectations (the known dispositions -- these runs prove the opt-out path, not new
physics):
  E_probe   -> builds past the tripwire; expected rc=2 (E-1 hold not visibly shown [anchor=ref-pose + gripper
               masking, banked v1.8/v1.9]; E-2/E-3/E-4 sync-level PASS as banked 5b9fe8e62c).
  E1v2      -> builds past the tripwire; expected rc=3 (the HV gate fires the known ENV-MULTIWORLD freeze
               [by-construction CPU path, banked 100997a44a] -- worlds 1-3 do not lift).
A tripwire refusal (RuntimeError at build) in either = the positive control FAILS.

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/forkb_i0a_positive_controls.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
OUT = _EVAL / "forkb_i0a_positive_controls_result.json"


def _run(mod_name, out_name, expect_rc):
    spec = importlib.util.spec_from_file_location(mod_name, _EVAL / f"{mod_name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)  # module-level opt-out lines activate here
    m.OUT = _EVAL / out_name  # redirect: the banked artifact is never overwritten
    rc = None
    try:
        rc = m.main()
    except SystemExit as e:
        rc = int(e.code or 0)
    except RuntimeError as e:
        if "single-world CPU template" in str(e):
            return {"probe": mod_name, "rc": "TRIPWIRE_REFUSED", "expect_rc": expect_rc, "PASS": False}
        raise
    return {"probe": mod_name, "rc": rc, "expect_rc": expect_rc, "PASS": rc == expect_rc, "fresh_artifact": out_name}


def main():
    results = [
        _run("pin_multiworld_E_probe", "pin_multiworld_E_probe_result_postI0a.json", 2),
        _run("pin_multiworld_E1v2_release_contrast", "pin_multiworld_E1v2_release_contrast_result_postI0a.json", 3),
    ]
    ok = all(r["PASS"] for r in results)
    out = {
        "MARK": "I0-a positive controls (D1 sec 4:78) -- fresh runs under the live tripwire, opt-out active",
        "pre_declared": "E_probe rc=2 (banked disposition), E1v2 rc=3 (known ENV-MULTIWORLD freeze)",
        "results": results,
        "ALL_PASS": ok,
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
