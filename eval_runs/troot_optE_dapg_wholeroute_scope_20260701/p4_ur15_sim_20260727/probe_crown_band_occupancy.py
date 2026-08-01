"""Where do the arms pass through the crown band, in the one pose that survives?

p5 §27-4.  At the only mounting of the twenty-four that met all three conditions -- no crown,
spread 0.280, tilt 20 -- the left arm keeps exactly one clear start pose.  The question is not
whether a smaller or lower head fits (both were swept and neither did) but whether the band the
head would occupy has room the arms do not use.  If it has, the room names a shape.  If it has
not, shape is finished too.

BAND: x in [-0.280, +0.280], z in [1.330, 1.530].  That is the span between the two mounts and
the height from the built underside to the mounts.

⚠ BOTH ARMS are reported.  A head is one body across the whole band, so a gap that only the left
arm leaves is not a gap.  p5 asked about the left arm; the right one is here because the answer
is about the band, not about an arm.

⛔ THE FIRST VERSION OF THIS PROBE WAS VOID, and the reason is worth keeping.  It took each
geom's axis-aligned box from the bounding SPHERE, and a forearm's bounding sphere is a ball the
size of the forearm -- 0.7 m across.  Every cell came out occupied, 0% free, which is what that
instrument would report for almost any pose.  A map that cannot come out differently is not a
map.  The conservatism was in the safe direction and it still destroyed the question.

So occupancy is measured instead: a 1 mm probe sphere is placed at each cell centre on the plane
y = 0 and mj_geomDistance -- the driver's own instrument -- reports its distance to the nearest
arm geom.  The number per cell is then the real clearance a head would have there, not a claim
about a box.

⛔ No run and no solve: the poses are the ones the driver printed, fed back in.
"""

from __future__ import annotations

import sys
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

SRC = Path("/tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-19a6-4bca-8043-e6731b3f2141/"
           "scratchpad/_steps_cell_full.xml")
# The driver writes the model with bare mesh names for the gripper, which resolve against the
# model file's own directory.  The pool it used is gone, so the model is staged in the gripper
# asset directory instead -- same files, and the bytes of the model are unchanged.
STAGED = Path("/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/assets"
              "/_as_built_band.xml")

# The poses the driver chose and printed, at (crown none, spread 0.280, tilt 20).
Q = {"L": [-0.100947, +0.995789, +1.570038, +0.341132, +1.335156, -0.342917],
     "R": [+1.632079, -0.021987, +1.913694, +0.410246, +0.446266, -2.229218]}
J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
      "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
X0, X1, Z0, Z1 = -0.280, 0.280, 1.330, 1.530
CELL = 0.020


PROBE = ('  <body name="bandprobe" mocap="true" pos="0 0 5">\n'
         '    <geom name="bandprobe_g" type="sphere" size="0.001" contype="0" conaffinity="0"'
         ' rgba="1 0 0 0.3"/>\n'
         '  </body>\n')


def main() -> int:
    # the model with a movable 1 mm sphere added, so a real distance can be asked at each cell
    _x = SRC.read_text()
    assert "bandprobe" not in _x
    _i = _x.rindex("</worldbody>")
    STAGED.write_text(_x[:_i] + PROBE + _x[_i:])
    m = mujoco.MjModel.from_xml_path(str(STAGED))
    d = mujoco.MjData(m)
    for t, q in Q.items():
        for name, v in zip(J6, q):
            d.qpos[m.joint(f"{t}_{name}").qposadr[0]] = v
    mujoco.mj_forward(m, d)

    bname = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, i) or "" for i in range(m.nbody)]

    def side(g):
        b = bname[m.geom_bodyid[g]]
        return b[0] if (b[:2] in ("L_", "R_") or b[:3] in ("Lg_", "Rg_")) else None

    nx = int(round((X1 - X0) / CELL))
    nz = int(round((Z1 - Z0) / CELL))
    pg = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "bandprobe_g")
    assert pg >= 0
    armg = {t: [g for g in range(m.ngeom) if side(g) == t] for t in ("L", "R")}
    clear = np.zeros((nz, nx))
    owner = [["." for _ in range(nx)] for _ in range(nz)]
    per_link = {}
    for iz in range(nz):
        for ix in range(nx):
            d.mocap_pos[0] = [X0 + (ix + 0.5) * CELL, 0.0, Z0 + (iz + 0.5) * CELL]
            mujoco.mj_forward(m, d)
            best, who = 1e9, "."
            for t in ("L", "R"):
                for g in armg[t]:
                    dv = mujoco.mj_geomDistance(m, d, pg, g, 1.0, None)
                    if dv < best:
                        best, who = dv, t
                        per_link.setdefault(bname[m.geom_bodyid[g]], 1e9)
            clear[iz, ix] = best
            owner[iz][ix] = who
    # symbol by how much room a head would have at that cell
    def sym(v, w):
        if v <= 0.0:
            return "#"                      # the arm is there
        if v < 0.010:
            return w.lower()                # under 10 mm
        if v < 0.030:
            return w                        # 10-30 mm
        return "+"                          # 30 mm or more
    grid = [[sym(clear[iz][ix], owner[iz][ix]) for ix in range(nx)] for iz in range(nz)]

    out = ["CROWN BAND OCCUPANCY -- the one surviving pose, at (crown none, spread 0.280, tilt 20)",
           f"band: x [{X0:+.3f}, {X1:+.3f}]  z [{Z0:.3f}, {Z1:.3f}]   cell {CELL*1000:.0f} mm",
           "poses: the driver's own chosen start poses, printed by it and fed back in --",
           f"  L q = {Q['L']}",
           f"  R q = {Q['R']}",
           "measured: a 1 mm probe sphere at each cell centre on the plane y=0, and the driver's",
           "  own mj_geomDistance to the nearest arm geom.  The symbol is that real clearance.",
           "⛔ The first version of this probe used bounding-sphere boxes and reported 0% free --",
           "  a forearm's bounding sphere is 0.7 m across, so every cell was 'occupied' and the",
           "  map could not have come out differently.  That version was discarded, not reported.",
           "⚠ This is a slice at y=0.  A head has thickness; the clearance quoted is the radius of",
           "  a sphere that fits at that cell, which bounds what a thicker body can do there.",
           "",
           "# = the arm is in the cell   l/r = under 10 mm to the left/right arm",
           "L/R = 10-30 mm   + = 30 mm or more of room",
           ""]
    hdr = "        " + "".join(f"{X0 + (i + 0.5) * CELL:+.2f}"[1:4] for i in range(nx))
    out.append(hdr)
    for iz in range(nz - 1, -1, -1):
        out.append(f"z{Z0 + (iz + 0.5) * CELL:6.3f}  " + "".join(f" {c} " for c in grid[iz]))
    out.append("")
    out.append("LINKS that were ever the nearest thing to a cell: " + ", ".join(sorted(per_link)))
    out.append("")
    inside = int((clear <= 0).sum())
    room30 = int((clear >= 0.030).sum())
    room10 = int((clear >= 0.010).sum())
    out.append(f"CELLS: {nx * nz} in the band.  {inside} have an arm in them.  "
               f"{room10} have 10 mm or more of room, {room30} have 30 mm or more.")
    out.append(f"largest clearance anywhere in the band: {clear.max()*1000:.1f} mm, at "
               f"x={X0 + (0.5 + int(np.argmax(clear) % nx)) * CELL:+.3f} "
               f"z={Z0 + (0.5 + int(np.argmax(clear) // nx)) * CELL:.3f}")
    out.append("⛔ Not a verdict.  What the free region can carry, if anything, is p5's call.")
    text = "\n".join(out) + "\n"
    (HERE / "CROWN_BAND_OCCUPANCY_20260802.txt").write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
