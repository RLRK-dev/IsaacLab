"""
全Phase FK検証スクリプト（カメラなし軽量版）
T1が計算した全Phase関節角度をIsaac Simで検証し、EE位置誤差 < 2cm を確認

各Phaseで:
1. 関節角度をテレポート適用
2. EE位置を取得
3. ウェイポイントと比較（Z offset +0.1034m 考慮）
4. 誤差を計算
"""

import argparse
import sys

# IsaacLab imports
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Verify all phases FK")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.sim import SimulationContext, SimulationCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

# Import all phase joint angles and waypoints from task_config
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
from configs.task_config import (
    LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,  # Phase 1
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS,
    PHASE4_LEFT_JOINTS, PHASE4_RIGHT_JOINTS,
    PHASE45_LEFT_JOINTS, PHASE45_RIGHT_JOINTS,
    PHASE5_LEFT_JOINTS, PHASE5_RIGHT_JOINTS,
    WAYPOINT_PHASE1_LEFT, WAYPOINT_PHASE1_RIGHT,
    WAYPOINT_PHASE2_LEFT, WAYPOINT_PHASE2_RIGHT,
    WAYPOINT_PHASE3_LEFT, WAYPOINT_PHASE3_RIGHT,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE, ROBOT_BASE_QUAT_WXYZ,
    GRIPPER_INIT,
)

# Z offset: Isaac Sim EE Z is waypoint Z + 0.1034m
Z_OFFSET = 0.1034

# Phase definitions
PHASES = [
    {
        "name": "Phase 1 (Hover)",
        "left_joints": LEFT_ARM_INIT_JOINTS,
        "right_joints": RIGHT_ARM_INIT_JOINTS,
        "left_waypoint": WAYPOINT_PHASE1_LEFT,
        "right_waypoint": WAYPOINT_PHASE1_RIGHT,
    },
    {
        "name": "Phase 2 (Grasp)",
        "left_joints": PHASE2_LEFT_JOINTS,
        "right_joints": PHASE2_RIGHT_JOINTS,
        "left_waypoint": WAYPOINT_PHASE2_LEFT,
        "right_waypoint": WAYPOINT_PHASE2_RIGHT,
    },
    {
        "name": "Phase 3 (Lift)",
        "left_joints": PHASE3_LEFT_JOINTS,
        "right_joints": PHASE3_RIGHT_JOINTS,
        "left_waypoint": WAYPOINT_PHASE3_LEFT,
        "right_waypoint": WAYPOINT_PHASE3_RIGHT,
    },
    {
        "name": "Phase 4 (Hook Approach)",
        "left_joints": PHASE4_LEFT_JOINTS,
        "right_joints": PHASE4_RIGHT_JOINTS,
        "left_waypoint": WAYPOINT_PHASE4_LEFT,
        "right_waypoint": WAYPOINT_PHASE4_RIGHT,
    },
    {
        "name": "Phase 4.5 (Intermediate)",
        "left_joints": PHASE45_LEFT_JOINTS,
        "right_joints": PHASE45_RIGHT_JOINTS,
        "left_waypoint": WAYPOINT_PHASE45_LEFT,
        "right_waypoint": WAYPOINT_PHASE45_RIGHT,
    },
    {
        "name": "Phase 5 (Placement)",
        "left_joints": PHASE5_LEFT_JOINTS,
        "right_joints": PHASE5_RIGHT_JOINTS,
        "left_waypoint": WAYPOINT_PHASE5_LEFT,
        "right_waypoint": WAYPOINT_PHASE5_RIGHT,
    },
]


# =============================================================================
# Minimal Scene Configuration (No Cameras)
# =============================================================================
@configclass
class MinimalLeftFrankaCfg(ArticulationCfg):
    """Minimal Left Franka configuration using standard USD"""
    prim_path = "{ENV_REGEX_NS}/Robot_Left"
    spawn = sim_utils.UsdFileCfg(
        usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd",
        activate_contact_sensors=False,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=True,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False,
            solver_position_iteration_count=4,
            solver_velocity_iteration_count=0,
        ),
    )
    init_state = ArticulationCfg.InitialStateCfg(
        pos=ROBOT_LEFT_BASE,
        rot=ROBOT_BASE_QUAT_WXYZ,
        joint_pos={
            "panda_joint1": LEFT_ARM_INIT_JOINTS[0],
            "panda_joint2": LEFT_ARM_INIT_JOINTS[1],
            "panda_joint3": LEFT_ARM_INIT_JOINTS[2],
            "panda_joint4": LEFT_ARM_INIT_JOINTS[3],
            "panda_joint5": LEFT_ARM_INIT_JOINTS[4],
            "panda_joint6": LEFT_ARM_INIT_JOINTS[5],
            "panda_joint7": LEFT_ARM_INIT_JOINTS[6],
            "panda_finger_joint.*": GRIPPER_INIT,
        },
        joint_vel={".*": 0.0},
    )
    actuators = {
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"],
            effort_limit=87.0,
            velocity_limit=2.175,
            stiffness=400.0,
            damping=40.0,
        ),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"],
            effort_limit=12.0,
            velocity_limit=2.61,
            stiffness=400.0,
            damping=40.0,
        ),
        "panda_hand": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger_joint.*"],
            effort_limit=200.0,
            velocity_limit=0.2,
            stiffness=4000.0,
            damping=100.0,
        ),
    }


@configclass
class MinimalRightFrankaCfg(ArticulationCfg):
    """Minimal Right Franka configuration using standard USD"""
    prim_path = "{ENV_REGEX_NS}/Robot_Right"
    spawn = sim_utils.UsdFileCfg(
        usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd",
        activate_contact_sensors=False,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=True,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False,
            solver_position_iteration_count=4,
            solver_velocity_iteration_count=0,
        ),
    )
    init_state = ArticulationCfg.InitialStateCfg(
        pos=ROBOT_RIGHT_BASE,
        rot=ROBOT_BASE_QUAT_WXYZ,
        joint_pos={
            "panda_joint1": RIGHT_ARM_INIT_JOINTS[0],
            "panda_joint2": RIGHT_ARM_INIT_JOINTS[1],
            "panda_joint3": RIGHT_ARM_INIT_JOINTS[2],
            "panda_joint4": RIGHT_ARM_INIT_JOINTS[3],
            "panda_joint5": RIGHT_ARM_INIT_JOINTS[4],
            "panda_joint6": RIGHT_ARM_INIT_JOINTS[5],
            "panda_joint7": RIGHT_ARM_INIT_JOINTS[6],
            "panda_finger_joint.*": GRIPPER_INIT,
        },
        joint_vel={".*": 0.0},
    )
    actuators = {
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"],
            effort_limit=87.0,
            velocity_limit=2.175,
            stiffness=400.0,
            damping=40.0,
        ),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"],
            effort_limit=12.0,
            velocity_limit=2.61,
            stiffness=400.0,
            damping=40.0,
        ),
        "panda_hand": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger_joint.*"],
            effort_limit=200.0,
            velocity_limit=0.2,
            stiffness=4000.0,
            damping=100.0,
        ),
    }


@configclass
class MinimalSceneCfg(InteractiveSceneCfg):
    """Minimal scene with just two robots - no cameras"""
    num_envs = 1
    env_spacing = 2.0

    # Ground
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    # Robots only
    robot_left: ArticulationCfg = MinimalLeftFrankaCfg()
    robot_right: ArticulationCfg = MinimalRightFrankaCfg()


def compute_error(actual, expected):
    """Compute Euclidean distance error in cm"""
    error = np.linalg.norm(np.array(actual) - np.array(expected))
    return error * 100  # Convert to cm


def main():
    print("=" * 70)
    print("全Phase FK検証 (Isaac Sim)")
    print("=" * 70)
    print(f"Z offset: +{Z_OFFSET}m (Isaac Sim EE Z = Waypoint Z + {Z_OFFSET})")
    print("=" * 70)

    # Create simulation context
    sim_cfg = SimulationCfg(dt=1/60, device="cuda:0")
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view(eye=[1.5, 0.0, 1.5], target=[0.4, 0.0, 0.85])

    # Create minimal scene (no cameras)
    scene_cfg = MinimalSceneCfg()
    scene = InteractiveScene(scene_cfg)

    # Play simulation
    sim.reset()

    # Get robot references
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]

    # Get panda_hand body index for EE position
    hand_idx_left = robot_left.find_bodies("panda_hand")[0][0]
    hand_idx_right = robot_right.find_bodies("panda_hand")[0][0]

    # Results storage
    results = []
    all_passed = True

    for phase in PHASES:
        print(f"\n--- {phase['name']} ---")

        # Prepare joint positions (7 arm joints + 2 gripper)
        left_joints = torch.tensor(
            [phase["left_joints"] + [0.04, 0.04]],
            dtype=torch.float32,
            device="cuda:0"
        )
        right_joints = torch.tensor(
            [phase["right_joints"] + [0.04, 0.04]],
            dtype=torch.float32,
            device="cuda:0"
        )

        # Set joint positions via teleport
        robot_left.write_joint_state_to_sim(left_joints, torch.zeros_like(left_joints))
        robot_right.write_joint_state_to_sim(right_joints, torch.zeros_like(right_joints))

        # Run simulation steps to settle
        for _ in range(30):
            sim.step()
            scene.update(sim.get_physics_dt())

        # Get actual EE positions
        left_ee_actual = robot_left.data.body_pos_w[0, hand_idx_left].cpu().numpy()
        right_ee_actual = robot_right.data.body_pos_w[0, hand_idx_right].cpu().numpy()

        # Expected EE positions (with Z offset)
        left_expected = (
            phase["left_waypoint"][0],
            phase["left_waypoint"][1],
            phase["left_waypoint"][2] + Z_OFFSET
        )
        right_expected = (
            phase["right_waypoint"][0],
            phase["right_waypoint"][1],
            phase["right_waypoint"][2] + Z_OFFSET
        )

        # Compute errors
        left_error = compute_error(left_ee_actual, left_expected)
        right_error = compute_error(right_ee_actual, right_expected)

        # Determine status
        left_ok = left_error < 2.0
        right_ok = right_error < 2.0
        phase_ok = left_ok and right_ok

        if not phase_ok:
            all_passed = False

        # Print results
        print(f"  Left EE:  ({left_ee_actual[0]:.4f}, {left_ee_actual[1]:.4f}, {left_ee_actual[2]:.4f})")
        print(f"  Expected: ({left_expected[0]:.4f}, {left_expected[1]:.4f}, {left_expected[2]:.4f})")
        print(f"  Right EE: ({right_ee_actual[0]:.4f}, {right_ee_actual[1]:.4f}, {right_ee_actual[2]:.4f})")
        print(f"  Expected: ({right_expected[0]:.4f}, {right_expected[1]:.4f}, {right_expected[2]:.4f})")
        print(f"  Error: Left={left_error:.2f}cm, Right={right_error:.2f}cm")
        print(f"  Status: {'OK' if phase_ok else 'FAILED'}")

        results.append({
            "phase": phase["name"],
            "left_actual": left_ee_actual,
            "left_expected": left_expected,
            "right_actual": right_ee_actual,
            "right_expected": right_expected,
            "left_error": left_error,
            "right_error": right_error,
            "status": "OK" if phase_ok else "FAILED"
        })

    # Summary
    print("\n" + "=" * 70)
    print("検証結果サマリー")
    print("=" * 70)
    for r in results:
        status_mark = "✓" if r["status"] == "OK" else "✗"
        print(f"{status_mark} {r['phase']}: Left={r['left_error']:.2f}cm, Right={r['right_error']:.2f}cm [{r['status']}]")

    print("=" * 70)
    if all_passed:
        print("全Phase検証: SUCCESS (全誤差 < 2cm)")
    else:
        print("全Phase検証: FAILED (一部誤差 >= 2cm)")
    print("=" * 70)

    # Cleanup
    simulation_app.close()

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
