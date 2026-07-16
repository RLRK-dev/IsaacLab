# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""V6 fails-without-fix: OLD (pre-I3/I4) behavior of the three new fixtures.

Pre-change artifact: runs ONLY at the I3/I4 commit PARENT (old ``_c1_escape_after_seat`` signature);
it breaks loudly at the post-fix commit -- that non-re-runnability IS the V6 point. Captured output =
``gate2_i3i4_v6_precheck_oldbehavior_output.txt``.
"""

import sys
from pathlib import Path

import numpy as np

_TIL = Path("/home/rlrk/IsaacLab/thread_isaac_lab")
for _p in (str(_TIL / "envs"), str(_TIL)):
    sys.path.insert(0, _p)

import newton_route_env as nre  # noqa: E402


def env27():
    e = object.__new__(nre.NewtonRouteEnv)
    e._pin_seat_seg = 27
    return e


C1X, C1Y = nre._C1_XY
C2X, C2Y = nre._C2_XY

# I3(a) fail-open: identity window {26,27} has NO C1Y crossing; a stray (segs 5-6, outside identity,
# out-of-groove laterally at +20mm but inside the 60mm DROP bar) is the only crossing.
a = np.zeros((40, 3))
a[:, 0] = 0.37
a[:, 1] = 0.30
a[:, 2] = 0.829
a[5] = (C1X + 0.020, C1Y + 0.010, 0.829)
a[6] = (C1X + 0.020, C1Y - 0.010, 0.829)

# I3(b) false escape: routed identity crossing (nodes 27-28) in-lateral (dx=0) but z OUT of band (0.90);
# stray (segs 5-6) IN-band z at +70mm dev. OLD global picker prefers in-band -> stray -> 70>60 -> True.
b = np.zeros((40, 3))
b[:, 0] = 0.37
b[:, 1] = 0.30
b[:, 2] = 0.90
b[27] = (C1X, C1Y + 0.010, 0.90)
b[28] = (C1X, C1Y - 0.010, 0.90)
b[5] = (C1X + 0.070, C1Y + 0.010, 0.829)
b[6] = (C1X + 0.070, C1Y - 0.010, 0.829)

# I4 feed-drape: routed side (below pin 27) Y-monotone down through C2Y at x = C2X+0.060 (60mm out);
# feed side (above pin) free span also Y-monotone down through C2Y, IN-groove at C2X.
c = np.zeros((40, 3))
c[:, 2] = 0.829
for i in range(40):
    c[i, 0] = C2X + 0.060
for i in range(28):
    c[i, 1] = 0.150 - (27 - i) * 0.015
for i in range(28, 40):
    c[i, 1] = 0.150 - (i - 27) * 0.015
    c[i, 0] = C2X
c[27, 0] = C2X + 0.060

e = env27()
print("I3(a) OLD escape (expect False = fail-open):", e._c1_escape_after_seat(a, True))
print("I3(b) OLD escape (expect True = false escape):", e._c1_escape_after_seat(b, True))
dx_a, z_a = e._seat_metrics(a, nre._C1_XY)
dx_b, z_b = e._seat_metrics(b, nre._C1_XY)
print(f"I3(a) identity metrics: dx={dx_a} (MISS sentinel=9.0?), z={z_a}")
print(f"I3(b) identity metrics: dx={dx_b:.4f} (in-lateral), z={z_b:.3f} (out-of-band)")
dx_c, z_c = e._seat_metrics(c, nre._C2_XY)
print(
    f"I4 feed-drape OLD: dx={dx_c:.4f}, z={z_c:.3f}, "
    f"seated={e._seated_in_groove(dx_c, z_c)} (expect True = wrong credit)"
)
segs = e._seat_identity_segments(c, nre._C2_XY)
print("I4 OLD admitted candidate segs (both sides):", segs)
