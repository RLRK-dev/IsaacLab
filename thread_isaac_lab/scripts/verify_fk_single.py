#!/usr/bin/env python3
"""Verify FK for a single arm. Spawn, reset, read EE, exit."""
from __future__ import annotations
import argparse, sys

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=str, default="cuda:0")
parser.add_argument("--side", type=str, default="left", choices=["left", "right_mirror", "right_ik"])
args, _ = parser.parse_known_args()

# Flush prints immediately
import functools
print = functools.partial(print, flush=True)

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=True, device=args.device, enable_cameras=True)
sim_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.utils import configclass
from thread_isaac_lab.configs.task_config import PHYSICS_DT

VGROOVE_URDF = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/robots/panda_independent_fingers.urdf"
BASE_QUAT = (0.7071, 0, 0.7071, 0)

CONFIGS = {
    "left": {
        "base": (0.2467, -0.5, 1.265),
        "joints": [0.650477, 0.698145, 0.100584, -1.909314, -2.356371, 1.924273, 1.914357],
    },
    "right_mirror": {
        "base": (0.2467, 0.5, 1.265),
        "joints": [-0.650477, 0.698145, -0.100584, -1.909314, 2.356371, 1.924273, -1.914357],
    },
    "right_ik": {
        "base": (0.2467, 0.5, 1.265),
        "joints": [-0.693292, 0.696613, -0.054122, -1.906359, 2.340102, 1.941590, -0.358249],
    },
}

cfg = CONFIGS[args.side]

@configclass
class RobotCfg(ArticulationCfg):
    prim_path = "{ENV_REGEX_NS}/Robot"
    spawn = sim_utils.UrdfFileCfg(
        asset_path=VGROOVE_URDF, fix_base=True, make_instanceable=False, activate_contact_sensors=False,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=True, max_depenetration_velocity=5.0),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True, solver_position_iteration_count=8, solver_velocity_iteration_count=0),
        joint_drive=sim_utils.UrdfConverterCfg.JointDriveCfg(
            gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(stiffness=None, damping=None)),
    )
    init_state = ArticulationCfg.InitialStateCfg(
        pos=cfg["base"], rot=BASE_QUAT,
        joint_pos={"panda_joint1": cfg["joints"][0], "panda_joint2": cfg["joints"][1],
                   "panda_joint3": cfg["joints"][2], "panda_joint4": cfg["joints"][3],
                   "panda_joint5": cfg["joints"][4], "panda_joint6": cfg["joints"][5],
                   "panda_joint7": cfg["joints"][6], "panda_finger_joint.*": 0.04},
        joint_vel={".*": 0.0},
    )
    actuators = {
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"], effort_limit=87.0, velocity_limit=2.175, stiffness=400.0, damping=80.0),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"], effort_limit=12.0, velocity_limit=2.61, stiffness=400.0, damping=80.0),
        "panda_hand": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger_joint.*"], effort_limit=200.0, velocity_limit=0.2, stiffness=0.0, damping=100.0),
    }

@configclass
class SceneCfg(InteractiveSceneCfg):
    num_envs: int = 1
    env_spacing: float = 5.0
    ground = AssetBaseCfg(prim_path="/World/ground", spawn=sim_utils.GroundPlaneCfg(size=(10.0, 10.0)))
    robot = RobotCfg()

def main():
    device = f"cuda:{app_launcher.device_id}"
    print(f"[VERIFY] side={args.side} joints={cfg['joints']} base={cfg['base']}")

    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(
        device=device, dt=PHYSICS_DT,
        physx=sim_utils.PhysxCfg(solver_type=0, max_position_iteration_count=32, max_velocity_iteration_count=1,
                                  bounce_threshold_velocity=0.5, enable_stabilization=True)))
    scene = InteractiveScene(SceneCfg())
    sim.reset(); scene.reset()

    robot = scene["robot"]
    robot.write_joint_state_to_sim(robot.data.default_joint_pos, robot.data.default_joint_vel)
    robot.set_joint_position_target(robot.data.default_joint_pos)
    robot.write_data_to_sim()

    # Read BEFORE PD steps
    sim.step(); scene.update(sim.cfg.dt)
    hbl = robot.find_bodies("panda_hand")[0][0]
    ee0 = robot.data.body_pos_w[0, hbl, :3]
    jp0 = robot.data.joint_pos[0, :7]
    print(f"[VERIFY] Step 0: EE=({ee0[0]:.6f}, {ee0[1]:.6f}, {ee0[2]:.6f})")
    print(f"[VERIFY] Step 0: joints=[{', '.join(f'{j:.6f}' for j in jp0.cpu().numpy())}]")

    # PD stabilization
    for _ in range(49):
        sim.step(); scene.update(sim.cfg.dt)

    ee50 = robot.data.body_pos_w[0, hbl, :3]
    eq50 = robot.data.body_quat_w[0, hbl]
    jp50 = robot.data.joint_pos[0, :7]
    rp = robot.data.root_pos_w[0]
    rq = robot.data.root_quat_w[0]

    print(f"[VERIFY] Step 50: EE=({ee50[0]:.6f}, {ee50[1]:.6f}, {ee50[2]:.6f})")
    print(f"[VERIFY] Step 50: quat=({eq50[0]:.4f}, {eq50[1]:.4f}, {eq50[2]:.4f}, {eq50[3]:.4f})")
    print(f"[VERIFY] Step 50: joints=[{', '.join(f'{j:.6f}' for j in jp50.cpu().numpy())}]")
    print(f"[VERIFY] Root: pos=({rp[0]:.4f}, {rp[1]:.4f}, {rp[2]:.4f}) quat=({rq[0]:.4f}, {rq[1]:.4f}, {rq[2]:.4f}, {rq[3]:.4f})")

    # Joint delta from requested
    req = torch.tensor(cfg["joints"], device=device, dtype=torch.float32)
    delta = (jp50[:7] - req).abs()
    print(f"[VERIFY] Joint deltas: [{', '.join(f'{d:.6f}' for d in delta.cpu().numpy())}]")
    print(f"[VERIFY] Max joint delta: {delta.max().item():.6f} rad")

    print("[VERIFY] DONE")

if __name__ == "__main__":
    main()
    sim_app.close()
