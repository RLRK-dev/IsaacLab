#!/usr/bin/env python3
"""
グリッパーフレーム診断スクリプト

Franka Pandaのリンク構造とEEフレームの位置関係を確認する
"""

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Diagnose gripper frame positions")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
from envs.dual_arm_cfg import DualArmSceneCfg


def main():
    # Setup simulation
    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])

    # Create scene
    scene_cfg = DualArmSceneCfg(num_envs=1)
    scene_cfg.num_envs = 1
    scene = InteractiveScene(scene_cfg)

    # Reset and warm up
    sim.reset()
    for _ in range(50):
        sim.step()
    scene.update(sim.get_physics_dt())

    # Get robot reference
    robot = scene["robot_left"]

    print("\n" + "=" * 70)
    print("FRANKA PANDA GRIPPER FRAME DIAGNOSIS")
    print("=" * 70)

    # 1. List all body names
    print("\n[1] Body Names and Indices:")
    print("-" * 50)
    for i, name in enumerate(robot.body_names):
        print(f"  {i:2d}: {name}")

    # 2. Get body positions
    print("\n[2] Body Positions (World Frame):")
    print("-" * 50)
    body_pos = robot.data.body_pos_w[0]  # [num_bodies, 3]

    # Key bodies to check
    key_bodies = ["panda_link7", "panda_link8", "panda_hand",
                  "panda_leftfinger", "panda_rightfinger"]

    key_indices = {}
    for name in key_bodies:
        try:
            idx = robot.body_names.index(name)
            key_indices[name] = idx
            pos = body_pos[idx]
            print(f"  {name:20s} (idx={idx:2d}): [{pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f}]")
        except ValueError:
            print(f"  {name:20s}: NOT FOUND")

    # 3. Calculate offsets
    print("\n[3] Offsets (from panda_hand):")
    print("-" * 50)

    if "panda_hand" in key_indices:
        hand_pos = body_pos[key_indices["panda_hand"]]

        for name in ["panda_link8", "panda_leftfinger", "panda_rightfinger"]:
            if name in key_indices:
                other_pos = body_pos[key_indices[name]]
                offset = other_pos - hand_pos
                dist = torch.norm(offset).item()
                print(f"  panda_hand -> {name:20s}:")
                print(f"    Offset: [{offset[0]:.4f}, {offset[1]:.4f}, {offset[2]:.4f}]")
                print(f"    Distance: {dist:.4f}m ({dist*100:.2f}cm)")

    # 4. Finger center calculation
    print("\n[4] Finger Center (Clamp Position):")
    print("-" * 50)

    if "panda_leftfinger" in key_indices and "panda_rightfinger" in key_indices:
        left_finger_pos = body_pos[key_indices["panda_leftfinger"]]
        right_finger_pos = body_pos[key_indices["panda_rightfinger"]]
        finger_center = (left_finger_pos + right_finger_pos) / 2

        print(f"  Left finger:  [{left_finger_pos[0]:.4f}, {left_finger_pos[1]:.4f}, {left_finger_pos[2]:.4f}]")
        print(f"  Right finger: [{right_finger_pos[0]:.4f}, {right_finger_pos[1]:.4f}, {right_finger_pos[2]:.4f}]")
        print(f"  Center:       [{finger_center[0]:.4f}, {finger_center[1]:.4f}, {finger_center[2]:.4f}]")

        if "panda_hand" in key_indices:
            hand_pos = body_pos[key_indices["panda_hand"]]
            offset_to_center = finger_center - hand_pos
            dist_to_center = torch.norm(offset_to_center).item()
            print(f"\n  Offset from panda_hand to finger center:")
            print(f"    Offset: [{offset_to_center[0]:.4f}, {offset_to_center[1]:.4f}, {offset_to_center[2]:.4f}]")
            print(f"    Distance: {dist_to_center:.4f}m ({dist_to_center*100:.2f}cm)")

    # 5. Gripper state
    print("\n[5] Joint Positions (Gripper):")
    print("-" * 50)

    finger_joint_names = ["panda_finger_joint1", "panda_finger_joint2"]
    try:
        finger_joint_ids = robot.find_joints(finger_joint_names)[0]
        finger_joint_pos = robot.data.joint_pos[0, finger_joint_ids]
        print(f"  panda_finger_joint1: {finger_joint_pos[0].item():.4f}m")
        print(f"  panda_finger_joint2: {finger_joint_pos[1].item():.4f}m")
        print(f"  (0.04m = fully open, 0.0m = fully closed)")
    except:
        print("  Could not find finger joints")

    # 6. Body quaternions
    print("\n[6] Body Orientations (panda_hand):")
    print("-" * 50)

    if "panda_hand" in key_indices:
        hand_quat = robot.data.body_quat_w[0, key_indices["panda_hand"]]
        print(f"  Quaternion (wxyz): [{hand_quat[0]:.4f}, {hand_quat[1]:.4f}, {hand_quat[2]:.4f}, {hand_quat[3]:.4f}]")

    # 7. Recommendation
    print("\n[7] RECOMMENDATIONS:")
    print("-" * 50)

    if "panda_hand" in key_indices and "panda_leftfinger" in key_indices:
        hand_pos = body_pos[key_indices["panda_hand"]]
        left_finger_pos = body_pos[key_indices["panda_leftfinger"]]
        right_finger_pos = body_pos[key_indices["panda_rightfinger"]]
        finger_center = (left_finger_pos + right_finger_pos) / 2

        # Calculate actual Z offset
        z_offset = finger_center[2] - hand_pos[2]

        print(f"  Current FINGERTIP_OFFSET: 0.1123m (11.23cm)")
        print(f"  Actual Z offset (hand -> finger_center): {z_offset.item():.4f}m ({z_offset.item()*100:.2f}cm)")
        print(f"")

        if abs(z_offset.item() - 0.1123) > 0.01:
            print(f"  WARNING: Actual offset differs from FINGERTIP_OFFSET!")
            print(f"  Consider updating FINGERTIP_OFFSET to {abs(z_offset.item()):.4f}m")
        else:
            print(f"  OK: Offset values are consistent")

    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70 + "\n")

    simulation_app.close()


if __name__ == "__main__":
    main()
