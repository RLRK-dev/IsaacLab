# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Gate-2 rerun probe: FM3/FM4 tighten semantics at HEAD, computed on the canonical golden recording.

ACCEPT-side / reachability evidence for the /reward-design rerun (the author's unit test
test_route_reward_identity_guards.py covers the REJECT side):
  1. C1 seat (G3 leg): per-frame identity-window seat metrics on REAL cable states; divergence count vs the
     pre-tighten global-search semantics (segment_indices=None). Expected: seat reachable, dx << 3.5mm at the
     seated tail, zero real-route rejections introduced by the tighten.
  2. Pin-identity consistency: the crossing straddle segment on real frames lies in {pin-1, pin} (the
     canonical 81-cell claim), derived pin node cross-checked over the post-onset window.
  3. FM3 (escape guard): with c1_latched=True over ALL post-onset frames, zero false escapes on the golden
     route; |x_dev| margin vs the 60mm bar.
  4. C2 seat (G5/c2_honest leg): identity (monotone-connection) window metrics over the tail; reachable.
No GPU, no env physics -- pure numpy over the recording, via the live class methods (object.__new__).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_TIL = _HERE.parent.parent / "thread_isaac_lab"
for _p in (str(_TIL / "envs"), str(_TIL)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import newton_route_env as nre  # noqa: E402
import route_env_config as rc  # noqa: E402

GOLDEN = _HERE / "w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz"
STRIDE = 10

SEC_S_NOTE = (
    "gate-2 rerun artifact: this probe VALIDATES the swept FM3/FM4 semantics (owner chain leg 1, "
    "I0A_SCOPE_MANIFEST:45); until the chain completes, HEAD reward semantics stay unratified (sec S)."
)


def main():
    d = np.load(GOLDEN)
    cable = d["cable_xyz"].astype(np.float64)  # [F, 40, 3]
    pin_active = d["pin_active"].astype(int)
    phase_id = d["phase_id"].astype(int)
    n_frames = cable.shape[0]

    onset = int(np.argmax(pin_active == 1))
    assert pin_active[onset] == 1, "golden recording has no pin onset"

    # Derive the pinned seat NODE from physics: at onset, the node holding y=C1Y in the groove box.
    c1x, c1y = float(nre._C1_XY[0]), float(nre._C1_XY[1])
    f0 = cable[onset]
    score = np.abs(f0[:, 0] - c1x) + np.abs(f0[:, 1] - c1y) + np.abs(f0[:, 2] - (rc.SEAT_Z_LO_M + 0.004))
    pin_node = int(np.argmin(score))
    # Cross-check stability of the derivation over 200 post-onset frames.
    stable = all(
        int(
            np.argmin(
                np.abs(cable[f][:, 0] - c1x)
                + np.abs(cable[f][:, 1] - c1y)
                + np.abs(cable[f][:, 2] - (rc.SEAT_Z_LO_M + 0.004))
            )
        )
        == pin_node
        for f in range(onset, min(onset + 200, n_frames), 20)
    )

    env = object.__new__(nre.NewtonRouteEnv)
    env._pin_seat_seg = pin_node

    frames = list(range(onset, n_frames, STRIDE))
    c1_dx = np.full(len(frames), np.nan)
    c1_z = np.full(len(frames), np.nan)
    seated_new = np.zeros(len(frames), dtype=bool)
    seated_old = np.zeros(len(frames), dtype=bool)
    escape_post = np.zeros(len(frames), dtype=bool)
    xdev = np.full(len(frames), np.nan)
    ipin_ok = 0
    ipin_n = 0
    for i, f in enumerate(frames):
        cp = cable[f]
        dx, z = env._seat_metrics(cp, nre._C1_XY)
        c1_dx[i], c1_z[i] = dx, z
        seated_new[i] = env._seated_in_groove(dx, z)
        # pre-tighten semantics: global straddle search (segment_indices=None)
        xo, zo = env._seat_crossing(cp, c1x, c1y, segment_indices=None)
        seated_old[i] = xo is not None and env._seated_in_groove(abs(xo - c1x), zo)
        # pin-identity consistency: which segments straddle C1Y at all
        y = cp[:, 1]
        straddle = np.nonzero(((y[:-1] - c1y) * (y[1:] - c1y)) <= 0.0)[0]
        if seated_new[i] and len(straddle):
            ipin_n += 1
            if any(s in (pin_node - 1, pin_node) for s in straddle):
                ipin_ok += 1
        escape_post[i] = env._c1_escape_after_seat(cp, True)
        dev = env._crossing_x_dev(cp)
        xdev[i] = np.nan if dev is None else dev

    # C2 tail (post final phases): identity = Y-monotone connection from the pin node
    c2_tail = [f for f in frames if phase_id[f] >= 9]
    c2_rows = []
    for f in c2_tail[-30:]:
        dx, z = env._seat_metrics(cable[f], nre._C2_XY)
        c2_rows.append((int(f), float(dx), float(z), bool(env._seated_in_groove(dx, z))))

    seat_frames = np.array(frames)[seated_new]
    tail = slice(-20, None)
    out = {
        "ts": time.time(),
        "golden": str(GOLDEN.relative_to(_HERE)),
        "n_frames": int(n_frames),
        "pin_onset_frame": onset,
        "derived_pin_node": pin_node,
        "pin_node_derivation_stable": bool(stable),
        "bars": {
            "SEAT_LAT_BAR_M": float(rc.SEAT_LAT_BAR_M),
            "SEAT_Z_LO_M": float(rc.SEAT_Z_LO_M),
            "SEAT_Z_HI_M": float(rc.SEAT_Z_HI_M),
            "DROP_LATERAL_DEV_MAX_M": float(nre.NewtonRouteEnv.DROP_LATERAL_DEV_MAX_M),
            "G_PHASE_BONUS": float(rc.G_PHASE_BONUS),
            "TERM_PENALTY": float(rc.TERM_PENALTY),
        },
        "c1_first_seated_frame": int(seat_frames[0]) if seat_frames.size else None,
        "c1_seated_fraction_post_onset": float(seated_new.mean()),
        "c1_dx_tail_mm": [round(v * 1000, 3) for v in c1_dx[tail]],
        "c1_z_tail": [round(v, 4) for v in c1_z[tail]],
        "tighten_divergence_frames": int(np.sum(seated_new != seated_old)),
        "old_semantics_seated_fraction": float(seated_old.mean()),
        "ipin_identity_consistency": f"{ipin_ok}/{ipin_n} seated frames have a straddle in {{pin-1,pin}}",
        "fm3_false_escape_frames_post_onset": int(escape_post.sum()),
        "fm3_max_abs_xdev_mm": float(np.nanmax(np.abs(xdev)) * 1000),
        "c2_tail_rows_frame_dxmm_z_seated": [(f, round(dx * 1000, 3), round(z, 4), s) for f, dx, z, s in c2_rows],
        "sec_S_note": SEC_S_NOTE,
    }
    (_HERE / "gate2_rerun_fm34_probe_result.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
