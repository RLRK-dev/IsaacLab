import os, sys
from pathlib import Path
_SCRIPTS = Path(sys.argv[1]).resolve()  # worktree thread_isaac_lab
for _p in (str(_SCRIPTS), str(_SCRIPTS / "envs")):
    sys.path.insert(0, _p)
os.environ.setdefault("MUJOCO_GL", "egl")
# NOTE: no ARM_PD_DRIVE -> baseline build
import newton_route_env as nre
import mujoco
env = nre.NewtonRouteEnv(world_count=1, device="cuda:0", cfg={
    "grasp_actuation": True, "route_executor_impl": "route_executor",
    "route_recording_npz": sys.argv[2], "g1_scene_align": True,
    "route_drive_mode": "feedforward", "route_c2_scene": True, "route_c1_pin": True})
m = env._solver.mj_model
print(f"nu={m.nu}")
for a in range(m.nu):
    j = int(m.actuator_trnid[a, 0])
    jn = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j)
    print(f"  act{a}: gain0={float(m.actuator_gainprm[a,0]):.1f} bias1={float(m.actuator_biasprm[a,1]):.1f} bias2={float(m.actuator_biasprm[a,2]):.1f} -> joint {j} ({jn})")
