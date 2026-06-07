"""calc_downward_joints.py — Calculate CLIP_APPROACH joints with downward orientation.

Spawns left and right Franka with current CLIP_APPROACH joints, then runs
pose-mode DiffIK to rotate EE to HAND_DOWN_QUAT while maintaining XYZ position.
Outputs the converged joint values for task_config.py update.
"""
from __future__ import annotations

import argparse
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=str, default="cuda:0")
parser.add_argument("--headless", action="store_true", default=False)
args, _ = parser.parse_known_args()

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=args.headless, device=args.device,
                           enable_cameras=False)
sim_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.utils import configclass
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.utils.math import matrix_from_quat, quat_inv, subtract_frame_transforms

from thread_isaac_lab.configs.task_config import (
    PHYSICS_DT,
    ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE, ROBOT_BASE_QUAT_WXYZ,
    CLIP_APPROACH_LEFT_JOINTS, CLIP_APPROACH_RIGHT_JOINTS,
    TABLE_HEIGHT,
)

VGROOVE_URDF = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/robots/panda_independent_fingers.urdf"
ARM_JOINT_IDS = list(range(7))
N_SIM_PER_IK = 4
HAND_DOWN_QUAT_WXYZ = (0.0, 0.7071, 0.7071, 0.0)
MAX_IK_STEPS = 2000  # More steps for large displacement + rotation

# P1-APPROACH target EE positions (from test_clip_routing.py)
APPROACH_TARGET_LEFT = (0.300, -0.170, 0.912)
APPROACH_TARGET_RIGHT = (0.300, +0.070, 0.912)


def make_franka_cfg(prim_path, base_pos, init_joints):
    @configclass
    class FrankaCfg(ArticulationCfg):
        pass

    cfg = FrankaCfg()
    cfg.prim_path = prim_path
    cfg.spawn = sim_utils.UrdfFileCfg(
        asset_path=VGROOVE_URDF,
        fix_base=True,
        make_instanceable=False,
        activate_contact_sensors=False,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=True,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=8,
            solver_velocity_iteration_count=0,
        ),
        joint_drive=sim_utils.UrdfConverterCfg.JointDriveCfg(
            gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(
                stiffness=None, damping=None,
            )
        ),
    )
    cfg.init_state = ArticulationCfg.InitialStateCfg(
        pos=base_pos,
        rot=ROBOT_BASE_QUAT_WXYZ,
        joint_pos={
            "panda_joint1": init_joints[0],
            "panda_joint2": init_joints[1],
            "panda_joint3": init_joints[2],
            "panda_joint4": init_joints[3],
            "panda_joint5": init_joints[4],
            "panda_joint6": init_joints[5],
            "panda_joint7": init_joints[6],
            "panda_finger_joint.*": 0.04,
        },
        joint_vel={".*": 0.0},
    )
    cfg.actuators = {
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"],
            effort_limit=87.0,
            velocity_limit=2.175,
            stiffness=400.0,
            damping=80.0,
        ),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"],
            effort_limit=12.0,
            velocity_limit=2.61,
            stiffness=400.0,
            damping=80.0,
        ),
        "panda_hand": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger_joint.*"],
            effort_limit=200.0,
            velocity_limit=0.2,
            stiffness=0.0,
            damping=100.0,
        ),
    }
    return cfg


def quat_angle_deg(q1, q2):
    dot = (q1 * q2).sum().abs().clamp(max=1.0)
    return 2.0 * torch.acos(dot).item() * 180.0 / 3.14159265


def converge_to_downward(robot, device, label, hand_body_idx, jac_body_idx,
                         lambda_val=0.01, target_pos_override=None):
    """Run pose-mode DiffIK to converge to downward orientation (and optionally a target position)."""
    hbl = hand_body_idx
    jbl = jac_body_idx

    # Read init EE
    ee_init_pos = robot.data.body_pos_w[0, hbl, :3].clone()
    ee_init_quat = robot.data.body_quat_w[0, hbl].clone()
    print(f"\n[{label}] Init EE pos: ({ee_init_pos[0]:.6f}, {ee_init_pos[1]:.6f}, {ee_init_pos[2]:.6f})")
    print(f"[{label}] Init EE quat (wxyz): ({ee_init_quat[0]:.4f}, {ee_init_quat[1]:.4f}, "
          f"{ee_init_quat[2]:.4f}, {ee_init_quat[3]:.4f})")

    # Target position: same as current or override
    if target_pos_override is not None:
        target_pos = torch.tensor([target_pos_override], dtype=torch.float32, device=device)
        print(f"[{label}] Target pos override: ({target_pos[0,0]:.4f}, {target_pos[0,1]:.4f}, {target_pos[0,2]:.4f})")
    else:
        target_pos = ee_init_pos.clone().unsqueeze(0)  # (1, 3)
    target_quat = torch.tensor([HAND_DOWN_QUAT_WXYZ], dtype=torch.float32, device=device)

    init_ori_err = quat_angle_deg(ee_init_quat, target_quat[0])
    print(f"[{label}] Init ori error: {init_ori_err:.1f} deg, lambda={lambda_val}")

    # Create pose-mode IK controller
    ik_cfg = DifferentialIKControllerCfg(
        command_type="pose",
        use_relative_mode=False,
        ik_method="dls",
        ik_params={"lambda_val": lambda_val},
    )
    ik_ctrl = DifferentialIKController(ik_cfg, num_envs=1, device=device)

    for ik_step in range(MAX_IK_STEPS):
        ee_pose_w = robot.data.body_pose_w[:, hbl]
        root_pose_w = robot.data.root_pose_w

        ee_pos_b, ee_quat_b = subtract_frame_transforms(
            root_pose_w[:, 0:3], root_pose_w[:, 3:7],
            ee_pose_w[:, 0:3], ee_pose_w[:, 3:7],
        )

        tgt_pos_b, tgt_quat_b = subtract_frame_transforms(
            root_pose_w[:, 0:3], root_pose_w[:, 3:7],
            target_pos, target_quat,
        )

        ik_ctrl.set_command(
            torch.cat([tgt_pos_b, tgt_quat_b], dim=-1),
            ee_pos=ee_pos_b, ee_quat=ee_quat_b,
        )

        jacobian = robot.root_physx_view.get_jacobians()[:, jbl, :, ARM_JOINT_IDS]
        base_rot = root_pose_w[:, 3:7]
        base_rot_matrix = matrix_from_quat(quat_inv(base_rot))
        jacobian[:, :3, :] = torch.bmm(base_rot_matrix, jacobian[:, :3, :])
        jacobian[:, 3:, :] = torch.bmm(base_rot_matrix, jacobian[:, 3:, :])

        joint_pos = robot.data.joint_pos[:, ARM_JOINT_IDS]
        joint_pos_des = ik_ctrl.compute(ee_pos_b, ee_quat_b, jacobian, joint_pos)

        tgt = robot.data.joint_pos.clone()
        tgt[0, :7] = joint_pos_des[0]
        robot.set_joint_position_target(tgt)
        robot.write_data_to_sim()

        for _ in range(N_SIM_PER_IK):
            sim.step()
            scene.update(sim.cfg.dt)

        # Check convergence every 10 steps
        if ik_step % 10 == 0 or ik_step == MAX_IK_STEPS - 1:
            ee_now = robot.data.body_pos_w[0, hbl, :3]
            ee_quat_now = robot.data.body_quat_w[0, hbl]
            pos_err = torch.norm(ee_now - target_pos[0]).item() * 1000
            ori_err = quat_angle_deg(ee_quat_now, target_quat[0])
            dx = (ee_now[0] - ee_init_pos[0]).item() * 1000
            dy = (ee_now[1] - ee_init_pos[1]).item() * 1000
            dz = (ee_now[2] - ee_init_pos[2]).item() * 1000
            print(f"[{label}] step {ik_step:3d}: pos_err={pos_err:.2f}mm ori_err={ori_err:.2f}deg "
                  f"dXY=({dx:.2f},{dy:.2f})mm dZ={dz:.2f}mm")

            if pos_err < 1.0 and ori_err < 2.0:
                print(f"[{label}] CONVERGED at step {ik_step}")
                break

    # Final state
    ee_final = robot.data.body_pos_w[0, hbl, :3]
    ee_quat_final = robot.data.body_quat_w[0, hbl]
    final_joints = robot.data.joint_pos[0, :7].cpu().tolist()
    pos_err = torch.norm(ee_final - target_pos[0]).item() * 1000
    ori_err = quat_angle_deg(ee_quat_final, target_quat[0])
    dx = (ee_final[0] - ee_init_pos[0]).item() * 1000
    dy = (ee_final[1] - ee_init_pos[1]).item() * 1000

    print(f"\n[{label}] === FINAL ===")
    print(f"[{label}] EE pos: ({ee_final[0]:.6f}, {ee_final[1]:.6f}, {ee_final[2]:.6f})")
    print(f"[{label}] EE quat: ({ee_quat_final[0]:.4f}, {ee_quat_final[1]:.4f}, "
          f"{ee_quat_final[2]:.4f}, {ee_quat_final[3]:.4f})")
    print(f"[{label}] pos_err={pos_err:.3f}mm, ori_err={ori_err:.3f}deg")
    print(f"[{label}] XY drift: dX={dx:.2f}mm, dY={dy:.2f}mm")
    print(f"[{label}] Joint values: {[round(j, 6) for j in final_joints]}")

    return {
        "init_ee": [round(ee_init_pos[i].item(), 6) for i in range(3)],
        "init_quat": [round(ee_init_quat[i].item(), 6) for i in range(4)],
        "final_ee": [round(ee_final[i].item(), 6) for i in range(3)],
        "final_quat": [round(ee_quat_final[i].item(), 6) for i in range(4)],
        "final_joints": [round(j, 6) for j in final_joints],
        "pos_err_mm": round(pos_err, 3),
        "ori_err_deg": round(ori_err, 3),
        "xy_drift_mm": [round(dx, 2), round(dy, 2)],
    }


# --- Main ---
device = f"cuda:{app_launcher.device_id}"
print(f"[CALC] device={device}")

# Scene with both arms
@configclass
class DualArmSceneCfg(InteractiveSceneCfg):
    num_envs: int = 1
    env_spacing: float = 5.0

    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(10.0, 10.0)),
    )
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(intensity=1500.0, color=(1.0, 1.0, 1.0)),
    )

    robot_left: ArticulationCfg = make_franka_cfg(
        "{ENV_REGEX_NS}/Robot_Left", ROBOT_LEFT_BASE, CLIP_APPROACH_LEFT_JOINTS)
    robot_right: ArticulationCfg = make_franka_cfg(
        "{ENV_REGEX_NS}/Robot_Right", ROBOT_RIGHT_BASE, CLIP_APPROACH_RIGHT_JOINTS)


sim_cfg = sim_utils.SimulationCfg(
    device=device,
    dt=PHYSICS_DT,
    physx=sim_utils.PhysxCfg(
        solver_type=0,
        max_position_iteration_count=32,
        max_velocity_iteration_count=1,
        bounce_threshold_velocity=0.5,
        enable_stabilization=True,
    ),
)
sim = sim_utils.SimulationContext(sim_cfg)
scene = InteractiveScene(DualArmSceneCfg())

sim.reset()
scene.reset()

# Init + PD stabilization
for name in ("robot_left", "robot_right"):
    r = scene[name]
    r.write_joint_state_to_sim(r.data.default_joint_pos, r.data.default_joint_vel)
    r.set_joint_position_target(r.data.default_joint_pos)
    r.write_data_to_sim()  # Send PD targets to PhysX

for _ in range(50):
    sim.step()
    scene.update(sim.cfg.dt)
print("[CALC] PD stabilized")

# Find hand body indices
robot_left = scene["robot_left"]
robot_right = scene["robot_right"]

hbl_l = robot_left.find_bodies("panda_hand")[0][0]
jbl_l = hbl_l - 1
hbl_r = robot_right.find_bodies("panda_hand")[0][0]
jbl_r = hbl_r - 1
print(f"[CALC] Left: hand_body={hbl_l}, jac_body={jbl_l}")
print(f"[CALC] Right: hand_body={hbl_r}, jac_body={jbl_r}")

# Converge left arm to approach target position + downward orientation
print(f"\n[CALC] LEFT target: pos={APPROACH_TARGET_LEFT}, quat={HAND_DOWN_QUAT_WXYZ}")
result_left = converge_to_downward(robot_left, device, "LEFT", hbl_l, jbl_l,
                                    lambda_val=0.01,
                                    target_pos_override=APPROACH_TARGET_LEFT)

# Converge right arm independently (targets are NOT symmetric)
print(f"\n[CALC] RIGHT target: pos={APPROACH_TARGET_RIGHT}, quat={HAND_DOWN_QUAT_WXYZ}")
result_right = converge_to_downward(robot_right, device, "RIGHT", hbl_r, jbl_r,
                                     lambda_val=0.01,
                                     target_pos_override=APPROACH_TARGET_RIGHT)

# Summary
print("\n" + "=" * 80)
print("RESULTS FOR task_config.py UPDATE")
print("=" * 80)
print(f"\nCLIP_APPROACH_LEFT_JOINTS = {result_left['final_joints']}")
print(f"CLIP_APPROACH_RIGHT_JOINTS = {result_right['final_joints']}")
print(f"\nLeft:  pos_err={result_left['pos_err_mm']:.3f}mm, ori_err={result_left['ori_err_deg']:.3f}deg, "
      f"XY drift={result_left['xy_drift_mm']}mm")
print(f"Right: pos_err={result_right['pos_err_mm']:.3f}mm, ori_err={result_right['ori_err_deg']:.3f}deg, "
      f"XY drift={result_right['xy_drift_mm']}mm")

# Save results
output = {
    "old_left": list(CLIP_APPROACH_LEFT_JOINTS),
    "old_right": list(CLIP_APPROACH_RIGHT_JOINTS),
    "left": result_left,
    "right": result_right,
}
out_path = "data/calc_downward_joints.json"
os.makedirs("data", exist_ok=True)
with open(out_path, "w") as f:
    json.dump(output, f, indent=2)
print(f"\nSaved: {out_path}")

sim_app.close()
