import os, sys
os.environ.update(YOKE_SPREAD_OVERRIDE="0.28", TILT_DEG_OVERRIDE="20", CROWN_R_OVERRIDE="0.110")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, mujoco, kinonly_step_solve as K, ur15_cell_spec as spec
m, _ = K.build_cell(); d = mujoco.MjData(m); grp = K.geom_groups(m); K.require_non_empty(grp)
qadr = {t: [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")] for j in K.J6] for t in ("L", "R")}
def row(label, q):
    for t in ("L", "R"):
        for k, a in enumerate(qadr[t]): d.qpos[a] = q[k]
    mujoco.mj_forward(m, d)
    aa, pa = K.closest(m, d, grp["L"], grp["R"])
    e1, p1 = K.closest(m, d, grp["L"], grp["env"]); e2, p2 = K.closest(m, d, grp["R"], grp["env"])
    ee, pe = (e1, p1) if e1 <= e2 else (e2, p2)
    print(f"| {label} | {aa*1000:+.1f} ({pa}) | {ee*1000:+.1f} ({pe}) | "
          f"{'CLEAR' if min(aa, ee) > 0 else 'TOUCHING OR THROUGH'} |", flush=True)
print("| pose | arm<->arm mm (pair) | arm<->column/table mm (pair) | verdict |", flush=True)
print("|---|---|---|---|", flush=True)
row("qpos = 0 (both arms)", np.zeros(6))
row("spec.HOME_POSE (control)", np.asarray(spec.HOME_POSE, float))
print(f"[audit] mj_step calls: {K._MJ_STEP_CALLS}", flush=True)
