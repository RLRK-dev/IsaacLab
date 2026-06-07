#!/usr/bin/env python3
"""Verify URDF FK: spawn 3 arms, compare analytical FK vs sim FK."""
from __future__ import annotations
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=str, default="cuda:0")
args, _ = parser.parse_known_args()

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=True, device=args.device, enable_cameras=False)
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

LEFT_JOINTS = [0.650477, 0.698145, 0.100584, -1.909314, -2.356371, 1.924273, 1.914357]
MIRROR_JOINTS = [-0.650477, 0.698145, -0.100584, -1.909314, 2.356371, 1.924273, -1.914357]
IK_JOINTS = [-0.693292, 0.696613, -0.054122, -1.906359, 2.340102, 1.941590, -0.358249]

_SPAWN = sim_utils.UrdfFileCfg(
    asset_path=VGROOVE_URDF, fix_base=True, make_instanceable=False, activate_contact_sensors=False,
    rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=True, max_depenetration_velocity=5.0),
    articulation_props=sim_utils.ArticulationRootPropertiesCfg(
        enabled_self_collisions=True, solver_position_iteration_count=8, solver_velocity_iteration_count=0,
    ),
    joint_drive=sim_utils.UrdfConverterCfg.JointDriveCfg(
        gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(stiffness=None, damping=None)
    ),
)
_ACTUATORS = {
    "panda_shoulder": ImplicitActuatorCfg(
        joint_names_expr=["panda_joint[1-4]"], effort_limit=87.0, velocity_limit=2.175, stiffness=400.0, damping=80.0,
    ),
    "panda_forearm": ImplicitActuatorCfg(
        joint_names_expr=["panda_joint[5-7]"], effort_limit=12.0, velocity_limit=2.61, stiffness=400.0, damping=80.0,
    ),
    "panda_hand": ImplicitActuatorCfg(
        joint_names_expr=["panda_finger_joint.*"], effort_limit=200.0, velocity_limit=0.2, stiffness=0.0, damping=100.0,
    ),
}

def _jdict(j):
    return {"panda_joint1": j[0], "panda_joint2": j[1], "panda_joint3": j[2], "panda_joint4": j[3],
            "panda_joint5": j[4], "panda_joint6": j[5], "panda_joint7": j[6], "panda_finger_joint.*": 0.04}

@configclass
class LeftCfg(ArticulationCfg):
    prim_path = "{ENV_REGEX_NS}/Robot_Left"
    spawn = _SPAWN
    init_state = ArticulationCfg.InitialStateCfg(
        pos=(0.2467, -0.5, 1.265), rot=BASE_QUAT, joint_pos=_jdict(LEFT_JOINTS), joint_vel={".*": 0.0})
    actuators = _ACTUATORS

@configclass
class RightMirrorCfg(ArticulationCfg):
    prim_path = "{ENV_REGEX_NS}/Robot_Right_M"
    spawn = _SPAWN
    init_state = ArticulationCfg.InitialStateCfg(
        pos=(0.2467, 0.5, 1.265), rot=BASE_QUAT, joint_pos=_jdict(MIRROR_JOINTS), joint_vel={".*": 0.0})
    actuators = _ACTUATORS

@configclass
class RightIKCfg(ArticulationCfg):
    prim_path = "{ENV_REGEX_NS}/Robot_Right_IK"
    spawn = _SPAWN
    init_state = ArticulationCfg.InitialStateCfg(
        pos=(0.2467, 0.5, 1.265), rot=BASE_QUAT, joint_pos=_jdict(IK_JOINTS), joint_vel={".*": 0.0})
    actuators = _ACTUATORS

@configclass
class DiagSceneCfg(InteractiveSceneCfg):
    num_envs: int = 1
    env_spacing: float = 5.0
    ground = AssetBaseCfg(prim_path="/World/ground", spawn=sim_utils.GroundPlaneCfg(size=(10.0, 10.0)))
    dome_light = AssetBaseCfg(prim_path="/World/DomeLight", spawn=sim_utils.DomeLightCfg(intensity=1500.0))
    robot_left = LeftCfg()
    robot_right_m = RightMirrorCfg()
    robot_right_ik = RightIKCfg()


def main():
    device = f"cuda:{app_launcher.device_id}"
    sim_cfg = sim_utils.SimulationCfg(
        device=device, dt=PHYSICS_DT,
        physx=sim_utils.PhysxCfg(solver_type=0, max_position_iteration_count=32, max_velocity_iteration_count=1,
                                  bounce_threshold_velocity=0.5, enable_stabilization=True),
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(DiagSceneCfg())
    sim.reset()
    scene.reset()

    robots = {"left": scene["robot_left"], "right_mirror": scene["robot_right_m"], "right_ik": scene["robot_right_ik"]}
    for name, robot in robots.items():
        robot.write_joint_state_to_sim(robot.data.default_joint_pos, robot.data.default_joint_vel)
        robot.set_joint_position_target(robot.data.default_joint_pos)

    for _ in range(50):
        sim.step()
        scene.update(sim.cfg.dt)

    print("\n=== FK VERIFICATION ===\n")
    for name, robot in robots.items():
        hbl = robot.find_bodies("panda_hand")[0][0]
        ee = robot.data.body_pos_w[0, hbl, :3]
        eq = robot.data.body_quat_w[0, hbl]
        rp = robot.data.root_pos_w[0]
        rq = robot.data.root_quat_w[0]
        jp = robot.data.joint_pos[0, :7]

        print(f"--- {name} ---")
        print(f"  Root: pos=({rp[0]:.4f}, {rp[1]:.4f}, {rp[2]:.4f}) quat=({rq[0]:.4f}, {rq[1]:.4f}, {rq[2]:.4f}, {rq[3]:.4f})")
        print(f"  Joints: [{', '.join(f'{j:.6f}' for j in jp.cpu().numpy())}]")
        print(f"  EE: pos=({ee[0]:.6f}, {ee[1]:.6f}, {ee[2]:.6f})")
        print(f"  EE: quat=({eq[0]:.4f}, {eq[1]:.4f}, {eq[2]:.4f}, {eq[3]:.4f})")
        # Print link7 and link8 positions for debugging
        for bname in ["panda_link7"]:
            bi = robot.find_bodies(bname)[0][0]
            bp = robot.data.body_pos_w[0, bi, :3]
            print(f"  {bname}: ({bp[0]:.6f}, {bp[1]:.6f}, {bp[2]:.6f})")
        print()


if __name__ == "__main__":
    main()
    sim_app.close()
