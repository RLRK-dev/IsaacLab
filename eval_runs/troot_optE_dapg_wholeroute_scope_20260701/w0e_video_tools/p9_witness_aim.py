#!/usr/bin/env python3
"""%9 witness-aim: per-frame cable<->clip witness points for close-cam auto-aim + breach events.

Offline npz post-process (locked runner untouched). Per frame, per clip, per part:
min mj_geomDistance over the FREE capsule set with the witness point (fromto), where
FREE = all capsules minus the flanking pair {cap(v-1), cap(v)} of every pinned vertex v
fired by that frame (exclusion variant C — the flanking pair shares the forced vertex;
pre-pin all geoms count, mask prevention). The excluded pair is emitted separately as the
forced-column channel (nothing silent).

Sources of truth: clip_parts test_newton_clip_routing.py:1164-1170 (cz = CLIP1_Z + CLIP_FLOAT_Z);
capsule layout :985-996 (r=0.004, half=0.0075, local +Z); npz quat xyzw (meta).
Pin identity: pinned_body transitions while pin_active; body->node offset calibrated by
frozen-node displacement over the first pin window (assert both legs agree).

Outputs (out dir): witness.csv (frame,clip,part,dist_mm,cap,wx,wy,wz[m]) at --stride;
events.json (per clip/part breach intervals vs --bar with min/witness, scanned at stride);
forced.csv (per pin flanking-pair min dist per clip). Usage:
  p9_witness_aim.py CELL_DIR [--clips "C1=0.35,0.15;C2=0.40,0.075"] [--cz 0.820]
                    [--stride 10] [--bar -1.0] [--out OUT]
"""
import argparse
import json
from pathlib import Path

import mujoco
import numpy as np

R, HALF, NSEG = 0.004, 0.0075, 40
PART_OFF = [
    ("floor", (0.0, 0.0, 0.0025), (0.020, 0.015, 0.0025)),
    ("lowW-x", (-0.009, 0.0, 0.0125), (0.0015, 0.015, 0.0075)),
    ("lowW+x", (+0.009, 0.0, 0.0125), (0.0015, 0.015, 0.0075)),
    ("hiW-x", (-0.013, 0.0, 0.025), (0.002, 0.015, 0.005)),
    ("hiW+x", (+0.013, 0.0, 0.025), (0.002, 0.015, 0.005)),
]


def build(clips, cz):
    boxes = "".join(
        f'<geom name="{lb}:{nm}" type="box" pos="{cx+dx} {cy+dy} {cz+dz}" size="{hx} {hy} {hz}" '
        f'contype="0" conaffinity="0"/>'
        for lb, cx, cy in clips for nm, (dx, dy, dz), (hx, hy, hz) in PART_OFF
    )
    caps = "".join(
        f'<body name="n{e:02d}"><freejoint/><geom name="cap{e:02d}" type="capsule" pos="0 0 {HALF}" '
        f'size="{R} {HALF}" contype="0" conaffinity="0"/></body>' for e in range(NSEG)
    )
    return mujoco.MjModel.from_xml_string(
        f'<mujoco><option gravity="0 0 0"/><worldbody>{boxes}{caps}</worldbody></mujoco>')


def pin_schedule(z):
    """[(node, fire_frame)] from pinned_body transitions; offset via frozen-node check."""
    act, pb = z["pin_active"].astype(bool), z["pinned_body"].astype(int)
    if not act.any():
        return []
    frames = np.where(act)[0]
    fires, seen = [], set()
    for t in frames:
        if pb[t] >= 0 and pb[t] not in seen:
            seen.add(pb[t])
            fires.append((int(pb[t]), int(t)))
    b0, t0 = fires[0]
    t1 = fires[1][1] if len(fires) > 1 else len(pb)
    xyz = z["cable_xyz"][t0:t1]
    disp = np.linalg.norm(xyz - xyz[0], axis=2).max(axis=0)
    off = b0 - int(disp.argmin())
    assert disp[b0 - off] < 2e-3, f"frozen-node check failed: disp={disp[b0-off]*1e3:.2f}mm"
    return [(b - off, t) for b, t in fires]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cell_dir")
    ap.add_argument("--clips", default="C1=0.35,0.15;C2=0.40,0.075")
    ap.add_argument("--cz", type=float, default=0.820)
    ap.add_argument("--stride", type=int, default=10)
    ap.add_argument("--bar", type=float, default=-1.0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cell = Path(a.cell_dir)
    out = Path(a.out) if a.out else cell / "witness_aim"
    out.mkdir(parents=True, exist_ok=True)
    clips = []
    for tok in a.clips.split(";"):
        lb, xy = tok.split("=")
        cx, cy = (float(v) for v in xy.split(","))
        clips.append((lb, cx, cy))

    z = np.load(cell / "route_demo_raw.npz")
    pins = pin_schedule(z)
    m = build(clips, a.cz)
    d = mujoco.MjData(m)
    gcap = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"cap{e:02d}") for e in range(NSEG)]
    gbox = {(lb, nm): mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"{lb}:{nm}")
            for lb, _, _ in clips for nm, _, _ in PART_OFF}
    ft = np.zeros(6)
    T = len(z["cable_xyz"])
    pos_a, quat_a = z["cable_xyz"], z["cable_quat"]

    wit_rows, forced_rows = [], []
    open_ev, events = {}, []
    for t in range(0, T, a.stride):
        for e in range(NSEG):
            d.qpos[7 * e: 7 * e + 3] = pos_a[t][e]
            x, y, qz_, w = quat_a[t][e]
            d.qpos[7 * e + 3: 7 * e + 7] = (w, x, y, qz_)
        mujoco.mj_forward(m, d)
        excl = set()
        for v, tf in pins:
            if t >= tf:
                excl.update((max(v - 1, 0), min(v, NSEG - 1)))
        free = [e for e in range(NSEG) if e not in excl]
        for lb, _, _ in clips:
            for nm, _, _ in PART_OFF:
                gb = gbox[(lb, nm)]
                best, bk, bw = 1e9, -1, None
                for e in free:
                    dist = mujoco.mj_geomDistance(m, d, gcap[e], gb, 0.05, ft)
                    if dist < best:
                        best, bk = dist, e
                        bw = 0.5 * (ft[0:3] + ft[3:6])
                wit_rows.append((t, lb, nm, best * 1000, bk, *np.round(bw, 5)))
                key = (lb, nm)
                if best * 1000 < a.bar:
                    ev = open_ev.get(key)
                    if ev is None:
                        open_ev[key] = ev = {"clip": lb, "part": nm, "onset": t, "min_mm": 9e9}
                    if best * 1000 < ev["min_mm"]:
                        ev.update(min_mm=round(best * 1000, 3), min_frame=t, cap=bk,
                                  witness=[round(float(v), 5) for v in bw])
                elif key in open_ev:
                    ev = open_ev.pop(key)
                    ev["offset_frame"] = t
                    events.append(ev)
                if excl:
                    fmin = min(mujoco.mj_geomDistance(m, d, gcap[e], gb, 0.05, ft) for e in excl)
                    forced_rows.append((t, lb, nm, round(fmin * 1000, 3), sorted(excl)))
    for ev in open_ev.values():
        ev["offset_frame"] = None  # still breached at end
        events.append(ev)

    with open(out / "witness.csv", "w") as f:
        f.write("frame,clip,part,dist_mm,cap,wx,wy,wz\n")
        for r in wit_rows:
            f.write(",".join(str(v) for v in r) + "\n")
    with open(out / "forced.csv", "w") as f:
        f.write("frame,clip,part,forced_min_mm,excl_caps\n")
        for r in forced_rows:
            f.write(",".join(str(v).replace(",", "/") for v in r) + "\n")
    meta = {"cell": str(cell), "pins": [{"node": v, "fire_frame": tf} for v, tf in pins],
            "clips": [{"label": lb, "cx": cx, "cy": cy} for lb, cx, cy in clips],
            "cz": a.cz, "stride": a.stride, "bar_mm": a.bar, "n_frames": T,
            "exclusion": "variant C (flanking pair per pinned vertex, from fire frame)"}
    with open(out / "events.json", "w") as f:
        json.dump({"meta": meta, "events": sorted(events, key=lambda e: e["onset"])}, f, indent=1)
    print(f"[witness-aim] {cell.name}: pins={pins} events={len(events)} -> {out}")
    for ev in sorted(events, key=lambda e: e.get("min_mm", 0))[:8]:
        print(f"  {ev['clip']}/{ev['part']}: [{ev['onset']}..{ev['offset_frame']}] "
              f"min {ev['min_mm']}mm @cap{ev.get('cap')} f{ev.get('min_frame')} wit={ev.get('witness')}")


if __name__ == "__main__":
    main()
