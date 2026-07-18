import os, sys
import numpy as np
from pathlib import Path
_TIL = Path(sys.argv[1]).resolve()
for _p in (str(_TIL), str(_TIL / "envs")):
    sys.path.insert(0, _p)
os.environ.setdefault("MUJOCO_GL", "egl")
import newton_route_env as nre
import warp as wp

env = nre.NewtonRouteEnv(world_count=1, device="cuda:0", cfg={
    "grasp_actuation": True, "route_executor_impl": "route_executor",
    "route_recording_npz": sys.argv[2], "g1_scene_align": True,
    "route_drive_mode": "feedforward", "route_c2_scene": True, "route_c1_pin": True})
env.INIT_XY_NOISE = 0.0
env.reset()
wp.synchronize()
maps = env._arm_ow_maps
arm_qd = maps["arm_ow_qd_idx"]; arm_q = maps["arm_ow_q_idx"]

# (1) newton wiring at arm dofs (baseline)
m = env._model
print("[1] newton joint_target wiring at arm dofs (baseline):")
print("    mode:", m.joint_target_mode.numpy()[arm_qd].tolist())
print("    ke  :", m.joint_target_ke.numpy()[arm_qd].tolist())
print("    kd  :", m.joint_target_kd.numpy()[arm_qd].tolist())
print("    jtp :", np.round(env._control.joint_target_pos.numpy()[arm_qd], 4).tolist())
print("    q   :", np.round(env._state_0.joint_q.numpy()[arm_q], 4).tolist())

# (2) find the device-side mj data ctrl
s = env._solver
cand = [n for n in dir(s) if "data" in n.lower() or "mjw" in n.lower() or n == "d"]
print("[2] solver data attrs:", cand)
d = None
for n in ("mjw_data", "mj_data", "data", "d"):
    if hasattr(s, n):
        d = getattr(s, n); print(f"    using solver.{n}: {type(d)}"); break
if d is not None and hasattr(d, "ctrl"):
    c = d.ctrl
    c_np = c.numpy() if hasattr(c, "numpy") else np.asarray(c)
    print("    ctrl shape:", c_np.shape)
    print("    ctrl[:16]:", np.round(np.ravel(c_np)[:16], 4).tolist())

# (3) write joint_target_pos[arm] = q + 0.1 -> step -> does device ctrl move?
jtp = env._control.joint_target_pos.numpy()
q_now = env._state_0.joint_q.numpy()[arm_q]
jtp[arm_qd] = q_now + 0.1
env._control.joint_target_pos.assign(jtp)
env._physics_step_all()
wp.synchronize()
if d is not None and hasattr(d, "ctrl"):
    c_np2 = d.ctrl.numpy() if hasattr(d.ctrl, "numpy") else np.asarray(d.ctrl)
    print("[3] after jtp[arm]=q+0.1 and 1 physics frame:")
    print("    ctrl[:16]:", np.round(np.ravel(c_np2)[:16], 4).tolist())
q_after = env._state_0.joint_q.numpy()[arm_q]
print("    q moved by:", np.round(q_after - q_now, 5).tolist())
