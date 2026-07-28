"""A whole-cell still, from four viewpoints, at the pose the run starts in.

Rs asked what the robot looks like as a whole.  The run video is three panels chosen to judge a
grasp -- wide, close-up, overhead -- and the wide one is framed on the hands, so none of them
answers "what is this machine".  This renders the assembly itself: both arms on the yoke, the
column, the table, the cable and the clips, from four directions, with nothing cropped.

Read, not rebuilt: the model is the as-built cell the last run compiled, so this cannot show a
machine different from the one that ran.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from ur15_cell_spec import HOME_POSE  # noqa: E402

# The tint lives in the driver, not the spec module (it is a recording attribute, ratified there
# as such), so it is read out of the driver's source rather than retyped -- a colour copied by
# hand is a colour that can drift from the videos it is meant to match.
_SRC = (HERE / "ur15_steps_wired.py").read_text()
_TINT_L = re.search(r'ARM_TINT = \{"L": \(([^)]*)\)', _SRC).group(1)
_TINT_R = re.search(r'"R": \(([^)]*)\)', _SRC[_SRC.index("ARM_TINT = "):]).group(1)
ARM_TINT = {"L": tuple(float(v) for v in _TINT_L.split(",")),
            "R": tuple(float(v) for v in _TINT_R.split(","))}

AS_BUILT = Path("/tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-19a6-4bca-8043-e6731b3f2141/"
                "scratchpad/meshpool/_as_built_t42.xml")
SRC = Path("/tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-19a6-4bca-8043-e6731b3f2141/"
           "scratchpad/_steps_cell_full.xml")
J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
      "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
W, H = 1200, 880   # the model's offscreen buffer is 900 tall; stay inside it

# (label, azimuth, elevation, distance, lookat-z)
VIEWS = [("front  (+y toward the viewer)", 90.0, -12.0, 3.4, 1.05),
         ("three-quarter", 135.0, -18.0, 3.4, 1.05),
         ("side  (from the left arm's side)", 180.0, -10.0, 3.4, 1.05),
         ("top", 90.0, -80.0, 3.2, 0.90)]


def main() -> int:
    # keep the staged copy in step with whatever the last run compiled
    AS_BUILT.write_bytes(SRC.read_bytes())
    m = mujoco.MjModel.from_xml_path(str(AS_BUILT))
    d = mujoco.MjData(m)
    for t in ("L", "R"):
        for name, q in zip(J6, HOME_POSE):
            d.qpos[m.joint(f"{t}_{name}").qposadr[0]] = q
    # The run tints the arms at load time, not in the XML, so a still rendered from the file alone
    # comes out grey and would not match the videos Rs is judging.  Same tint, same exclusion: the
    # gripper geoms keep their own blue-top / red-bottom claws.
    for i in range(m.ngeom):
        b = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, m.geom_bodyid[i]) or ""
        if b[:2] in ("L_", "R_"):
            m.geom_rgba[i] = ARM_TINT[b[0]]
    mujoco.mj_forward(m, d)

    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    tiles = []
    with mujoco.Renderer(m, height=H, width=W) as r:
        for label, az, el, dist, lz in VIEWS:
            cam.azimuth, cam.elevation, cam.distance = az, el, dist
            cam.lookat[:] = [0.0, 0.1, lz]
            r.update_scene(d, camera=cam)
            tiles.append(r.render())
            print(f"[view] {label}: azimuth {az} elevation {el} distance {dist}")

    grid = np.vstack([np.hstack(tiles[:2]), np.hstack(tiles[2:])])
    out = HERE / "UR15_CELL_OVERVIEW_20260729.png"
    Image.fromarray(grid).save(out)
    print(f"[out] {out}  ({grid.shape[1]}x{grid.shape[0]})")
    print("[note] pose = the cell's home values, both arms; left arm ORANGE, right arm PURPLE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
