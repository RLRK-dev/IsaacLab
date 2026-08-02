# What does mj_geomDistance return for geoms that OVERLAP by a known amount?
# The grid's interleave column reads "+0.0" on most rows.  Before that is written up as
# "touching to within 0.05 mm" it has to be known whether 0.0 is a measurement or a floor.
import mujoco, numpy as np
XML = """<mujoco><worldbody>
 <body name="a" pos="0 0 0"><geom name="ga" type="box" size="0.05 0.05 0.05"/></body>
 <body name="b" pos="0 0 0"><joint type="slide" axis="0 0 1"/><geom name="gb" type="box" size="0.05 0.05 0.05"/></body>
 <body name="c" pos="0.5 0 0"><geom name="gc" type="capsule" size="0.02" fromto="0 0 0 0 0 0.2"/></body>
 <body name="e" pos="0.5 0 0"><joint type="slide" axis="1 0 0"/><geom name="ge" type="capsule" size="0.02" fromto="0 0 0 0 0 0.2"/></body>
</worldbody></mujoco>"""
m = mujoco.MjModel.from_xml_string(XML); d = mujoco.MjData(m)
ga, gb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "ga"), mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "gb")
gc, ge = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "gc"), mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "ge")
print(f"mujoco {mujoco.__version__}")
print("box vs box, separation swept from apart to deeply overlapped (cutoff 0.176 m as the run uses):")
for dz in (0.150, 0.101, 0.100, 0.090, 0.050, 0.010, 0.000, -0.020):
    d.qpos[0] = dz; mujoco.mj_forward(m, d)
    v = mujoco.mj_geomDistance(m, d, ga, gb, 0.176, None)
    print(f"   centres {dz:+.3f} m apart -> true gap {dz-0.10:+.4f} m, mj_geomDistance {v:+.6f}")
print("capsule vs capsule, same sweep in x (true gap = |dx| - 0.04):")
for dx in (0.100, 0.045, 0.040, 0.030, 0.010, 0.000):
    d.qpos[1] = dx; mujoco.mj_forward(m, d)
    v = mujoco.mj_geomDistance(m, d, gc, ge, 0.176, None)
    print(f"   centres {dx:+.3f} m apart -> true gap {dx-0.04:+.4f} m, mj_geomDistance {v:+.6f}")
