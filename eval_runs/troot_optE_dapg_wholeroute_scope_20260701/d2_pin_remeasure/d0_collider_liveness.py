# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""(d2) D0 -- is the RL env's C1 clip collider ALIVE at runtime? This must run BEFORE arm D.

WHY IT COMES FIRST (p5). Arm D changes the env's C1 contact stiffness from 2500 to the producer's 40000 and
asks whether the cable still escapes. But that question is only meaningful if the C1 geom PARTICIPATES IN
CONTACT at all. If its collider is dead, arm D changes a parameter on a geom that never touches anything:
the dynamics are unchanged, D comes out bit-identical to A, and the verdict table then says "INSTRUMENT DEAD
-- fix the flag wiring". That diagnosis would be WRONG. The wiring would be fine; the COLLIDER would be dead.
We would inspect the plumbing, find it correct, and stall.

⭐ Two different failures produce the SAME observable (cable escapes sideways, groove ends up empty):
     (1) the wall is 16x too soft  -> the cable pushes through it
     (2) the wall's collider is dead -> the cable never touches it at all
   D0 is what tells them apart. Without it, BOTH of arm D's verdicts are confounded.

⭐ AND D0 decides what everything else MEANS (p5):
     collider DEAD  -> "the groove is empty in every frame" is a SCENE defect; the artifact is rejectable.
     collider ALIVE -> a real physical groove was there, and the cable still ended up ~56mm away lying on the
                       base (z=824mm). That is a genuine route/grip failure -- and far more damning.

⚠ SOURCE EXISTENCE IS NOT RUNTIME LIVENESS. The Newton layer sets shape_flags = 0x6 (COLLIDE|BROADPHASE) for
the clip parts, and three of us read that as "the clips collide". But nobody read the MuJoCo layer the solver
actually steps. That is precisely the dead-mirror class from B3a: mjw_data EXISTED, and was never stepped, and
its zeros were mistaken for facts. So this probe reads MuJoCo's own contype/conaffinity, and then does the
thing that actually settles it -- watches for a real contact.

⭐ THE PROBE HAS ITS OWN POSITIVE CONTROL. A probe that reports "no contact" is worthless if it could not have
seen a contact in the first place. The env's C2 clip IS record-matched (ke=40000), so it is the control: if
C2 shows contact and C1 does not, C1's collider is dead. If NEITHER shows contact, the PROBE is dead and its
"no contact" means nothing -- exactly the trap this whole arc has been about.

Run: ROUTE_C2_SCENE=1 d0_collider_liveness.py --steps 400 --out d0_result.json   (cuda:0, env_isaaclab7)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def probe(env, steps: int) -> dict:
    """Read MuJoCo's own collision flags, then WATCH for a real cable<->clip contact."""
    import mujoco

    solver = env._solver
    mjm, mjd = getattr(solver, "mj_model", None), getattr(solver, "mj_data", None)
    if mjm is None or mjd is None:
        raise RuntimeError(
            f"solver exposes no mj_model/mj_data (use_mujoco_cpu={getattr(solver, 'use_mujoco_cpu', None)}) "
            "-- cannot read the buffer the solver actually steps. Refusing to guess from the Newton layer: "
            "that is the dead-mirror mistake (source existence != runtime liveness)."
        )

    # Name the geoms MuJoCo actually has. Clip parts and cable bodies are identified by label, never by index.
    names = [mujoco.mj_id2name(mjm, mujoco.mjtObj.mjOBJ_GEOM, i) or "" for i in range(int(mjm.ngeom))]

    def _sel(pred):
        return [i for i, n in enumerate(names) if pred(n.lower())]

    c1 = _sel(lambda n: "clip" in n and "c2" not in n and "clip2" not in n and "spacer" not in n)
    c2 = _sel(lambda n: ("c2" in n or "clip2" in n) and "spacer" not in n)
    cable = _sel(lambda n: "cable" in n or "rod" in n or "seg" in n)

    def _flags(ids):
        return {
            "n": len(ids),
            "contype_nonzero": int(sum(1 for i in ids if int(mjm.geom_contype[i]) != 0)),
            "conaffinity_nonzero": int(sum(1 for i in ids if int(mjm.geom_conaffinity[i]) != 0)),
            "contype": sorted({int(mjm.geom_contype[i]) for i in ids}),
            "conaffinity": sorted({int(mjm.geom_conaffinity[i]) for i in ids}),
        }

    static = {"C1": _flags(c1), "C2": _flags(c2), "cable": _flags(cable)}

    # THE PART THAT ACTUALLY SETTLES IT: a flag says a contact is permitted; only a contact says it happens.
    c1s, c2s, cabs = set(c1), set(c2), set(cable)
    hits = {"cable_C1": 0, "cable_C2": 0}
    fmax = {"cable_C1": 0.0, "cable_C2": 0.0}
    force = np.zeros(6, dtype=np.float64)
    for _ in range(int(steps)):
        env.step(env._zero_action() if hasattr(env, "_zero_action") else None)
        for k in range(int(mjd.ncon)):
            con = mjd.contact[k]
            g1, g2 = int(con.geom1), int(con.geom2)
            pair = None
            if (g1 in cabs and g2 in c1s) or (g2 in cabs and g1 in c1s):
                pair = "cable_C1"
            elif (g1 in cabs and g2 in c2s) or (g2 in cabs and g1 in c2s):
                pair = "cable_C2"
            if pair:
                mujoco.mj_contactForce(mjm, mjd, k, force)
                hits[pair] += 1
                fmax[pair] = max(fmax[pair], float(abs(force[0])))

    c1_alive = hits["cable_C1"] > 0
    c2_alive = hits["cable_C2"] > 0
    # The probe's own positive control: if C2 (record-matched, ke=40000) never contacts either, the PROBE is
    # dead and its silence about C1 means nothing.
    probe_alive = c2_alive or c1_alive
    return {
        "static_flags": static,
        "contacts_seen": hits,
        "max_normal_force_N": {k: round(v, 4) for k, v in fmax.items()},
        "C1_collider_alive": bool(c1_alive),
        "C2_collider_alive": bool(c2_alive),
        "PROBE_alive": bool(probe_alive),
        "verdict": (
            "PROBE DEAD -- neither C1 nor C2 ever contacted the cable. This probe cannot see contact at all, so "
            "its silence about C1 is not evidence. Fix the probe before reading anything into arm D."
            if not probe_alive
            else (
                "C1 collider ALIVE -- arm D is well-posed: changing its stiffness will change the dynamics."
                if c1_alive
                else "C1 collider DEAD (C2 contacts, C1 never does) -- arm D would be VACUOUS: it would change a "
                "parameter on a geom that never touches anything, come out identical to arm A, and be "
                "misread as a wiring bug. The scene, not the stiffness, is the defect."
            )
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--out", default="d0_collider_liveness.json")
    a = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "thread_isaac_lab" / "envs"))
    raise SystemExit(
        "D0 needs the env constructed by the (d2) runner (cfg: route_c2_scene=1 so C2 -- the probe's own "
        "positive control -- exists). Import probe() from the runner rather than building a second env here: "
        "a second construction path is a second thing to keep in sync, and this arc has paid for that already."
    )


if __name__ == "__main__":
    main()
