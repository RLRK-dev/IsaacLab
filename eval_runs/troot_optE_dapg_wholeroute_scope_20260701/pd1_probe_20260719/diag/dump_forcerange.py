import os, sys
import numpy as np
from pathlib import Path
_TIL = Path(sys.argv[1]).resolve()
for _p in (str(_TIL), str(_TIL / "envs")):
    sys.path.insert(0, _p)
os.environ.setdefault("MUJOCO_GL", "egl")
import newton_route_env as nre
env = nre.NewtonRouteEnv(world_count=1, device="cuda:0", cfg={
    "grasp_actuation": True, "route_executor_impl": "route_executor",
    "route_recording_npz": sys.argv[2], "g1_scene_align": True,
    "route_drive_mode": "feedforward", "route_c2_scene": True, "route_c1_pin": True})
m = env._solver.mj_model
print(f"nu={m.nu}")
fr = np.asarray(m.actuator_forcerange); frl = np.asarray(m.actuator_forcelimited)
cr = np.asarray(m.actuator_ctrlrange); crl = np.asarray(m.actuator_ctrllimited)
jfr = np.asarray(m.jnt_actfrcrange); jfrl = np.asarray(m.jnt_actfrclimited)
for a in range(m.nu):
    j = int(m.actuator_trnid[a, 0])
    print(f"  act{a}: gain0={float(m.actuator_gainprm[a,0]):.0f} forcelimited={int(frl[a])} forcerange=({fr[a,0]:.1f},{fr[a,1]:.1f}) ctrllimited={int(crl[a])} ctrlrange=({cr[a,0]:.2f},{cr[a,1]:.2f}) joint{j} jnt_actfrclimited={int(jfrl[j])} jnt_actfrcrange=({jfr[j,0]:.1f},{jfr[j,1]:.1f})")
# device model attr availability
s = env._solver
mm = getattr(s, "mjw_model", None)
print("mjw_model actuator_gainprm attr:", hasattr(mm, "actuator_gainprm"))
if hasattr(mm, "actuator_gainprm"):
    g = mm.actuator_gainprm
    g_np = g.numpy() if hasattr(g, "numpy") else np.asarray(g)
    print("  mjw gainprm shape:", g_np.shape, " gain0 col:", np.round(np.ravel(g_np.reshape(-1, g_np.shape[-1])[:, 0])[:16], 1).tolist())
