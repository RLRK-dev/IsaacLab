import os, sys
import numpy as np
from pathlib import Path
_TIL = Path(sys.argv[1]).resolve()
for _p in (str(_TIL), str(_TIL / "envs")):
    sys.path.insert(0, _p)
os.environ.setdefault("MUJOCO_GL", "egl")
mode = sys.argv[3]  # "pd" or "kin"
if mode == "pd":
    os.environ["ARM_PD_DRIVE"] = "1"
import warp as wp
import torch
import newton_route_env as nre
env = nre.NewtonRouteEnv(world_count=1, device="cuda:0", cfg={
    "grasp_actuation": True, "route_executor_impl": "route_executor",
    "route_recording_npz": sys.argv[2], "g1_scene_align": True,
    "route_drive_mode": "feedforward", "route_c2_scene": True, "route_c1_pin": True})
env.INIT_XY_NOISE = 0.0
env.reset()
wp.synchronize()
aq = env._arm_ow_maps["arm_ow_q_idx"]
def r(x): return np.round(np.asarray(x, dtype=float), 3).tolist()
print(f"[{mode}] POST-RESET:")
print("  q[arm]          =", r(env._state_0.joint_q.numpy()[aq]))
print("  _per_world_fk_jq[0][arm-local] =", r(np.asarray(env._per_world_fk_jq[0])[[0,1,2,3,4,5,14,15,16,17,18,19]]))
rec = getattr(env._route, "_recording", None)
if rec is not None and "arm_q" in rec:
    print("  recording arm_q[0] =", r(np.asarray(rec["arm_q"][0])[:12]))
    print("  recording arm_q keys:", list(rec.keys())[:12])
zero = torch.zeros((1, 6), dtype=torch.float32)
for t in range(2):
    env.step(zero)
    wp.synchronize()
    print(f"[{mode}] after step {t}: q[arm] =", r(env._state_0.joint_q.numpy()[aq]))
# device ctrl for live actuators (pd only)
s = env._solver
d = getattr(s, "mjw_data", None)
if d is not None and hasattr(d, "ctrl"):
    print(f"[{mode}] mjw ctrl[:16] =", r(np.ravel(d.ctrl.numpy())[:16]))
