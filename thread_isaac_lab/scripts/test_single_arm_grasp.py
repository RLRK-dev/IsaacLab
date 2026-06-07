#!/usr/bin/env python3
"""
シンプルな把持テスト
複雑なフェーズ制御を除外して、純粋にロボットがケーブルを把持できるか確認

修正版: グリッパー姿勢とターゲット位置の修正
"""

import argparse
import os
import torch
from PIL import Image
import numpy as np
import math

# Isaac Lab imports
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Simple grasp test")
parser.add_argument("--output_dir", type=str, default="/tmp/single_arm_grasp_test")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.utils.math import subtract_frame_transforms, quat_from_euler_xyz, quat_mul

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
from envs.dual_arm_cfg import DualArmSceneCfg

# Constants
GRIPPER_OPEN = 0.04
GRIPPER_CLOSE = 0.001  # Tighter grip to prevent slipping (was 0.005)
# TCP offset from panda_hand to fingertip center
# panda_hand -> finger_joint: 0.0584m
# finger_joint -> fingertip: ~0.045m
# Total nominal: 0.1123m
# Adding extra margin for better contact: +0.02m
FINGERTIP_OFFSET = 0.12  # Increased for better contact


def compute_grasp_quat_for_cable(cable_start, cable_end, device):
    """
    ケーブルの方向に基づいてグリッパーの姿勢を計算。
    グリッパーの指がケーブルに垂直になるように回転。

    Franka Pandaのグリッパー:
    - panda_handフレームでは指はY軸方向に開閉
    - グリッパーが下を向いた状態 (Z軸が下向き) にするにはX軸周りに180°回転
    - 指がケーブル (X軸方向) に垂直になるには、追加のZ軸回転は不要

    Args:
        cable_start: ケーブルの始点位置
        cable_end: ケーブルの終点位置 (または次のセグメント位置)
        device: torch device

    Returns:
        グリッパーのターゲットクォータニオン (wxyz形式)
    """
    # ケーブルの方向ベクトル (XY平面上)
    cable_dir = cable_end - cable_start
    cable_dir[2] = 0  # Z成分を無視 (水平方向のみ考慮)
    cable_dir_norm = torch.norm(cable_dir)

    if cable_dir_norm < 1e-6:
        # ケーブルがほぼ垂直の場合、デフォルト姿勢を使用
        cable_yaw = 0.0
    else:
        cable_dir = cable_dir / cable_dir_norm
        # ケーブルの向きからYaw角を計算
        cable_yaw = torch.atan2(cable_dir[1], cable_dir[0]).item()

    # グリッパーの指 (Y軸方向に開閉) がケーブルに垂直になるように:
    # - ケーブルがX軸方向 (yaw=0) の場合、グリッパーのyaw=0で指はY軸方向 → 垂直 ✓
    # - ケーブルがY軸方向 (yaw=90°) の場合、グリッパーのyaw=90°で指はX軸方向 → 垂直 ✓
    # つまり、グリッパーのyaw = ケーブルのyaw (追加回転不要)
    gripper_yaw = cable_yaw

    print(f"  [Quat] Cable direction: yaw={math.degrees(cable_yaw):.1f}°")
    print(f"  [Quat] Gripper target yaw: {math.degrees(gripper_yaw):.1f}°")

    # オイラー角からクォータニオンを生成 (XYZ順)
    # Roll: 180° (グリッパーを下向きに - Z軸が下を向く)
    # Pitch: 0°
    # Yaw: gripper_yaw
    roll = torch.tensor([math.pi], device=device)   # 180° - 下向き
    pitch = torch.tensor([0.0], device=device)
    yaw = torch.tensor([gripper_yaw], device=device)

    # quat_from_euler_xyz は (roll, pitch, yaw) を受け取り wxyz形式で返す
    quat = quat_from_euler_xyz(roll, pitch, yaw)

    print(f"  [Quat] Result (wxyz): {quat[0].cpu().tolist()}")
    return quat


class SimpleGraspTester:
    """Simple test for single-arm cable grasping."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Setup simulation (following working pattern from collect_with_claude_direct.py)
        sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0)
        self.sim = sim_utils.SimulationContext(sim_cfg)
        self.sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])
        self.device = self.sim.device

        # Create scene
        scene_cfg = DualArmSceneCfg(num_envs=1)
        scene_cfg.env_spacing = 4.0
        self.scene = InteractiveScene(scene_cfg)

        # Reset simulation after scene creation (important!)
        self.sim.reset()

        # Warm up simulation
        print("[Tester] Running warm-up steps...")
        for _ in range(30):
            self.sim.step()
        self.scene.update(self.sim.get_physics_dt())

        # Get robot references
        self.robot_left = self.scene["robot_left"]
        self.cable = self.scene["cable"]

        # Camera references
        self.front_left_cam = self.scene["front_left_camera"]
        self.overhead_cam = self.scene["overhead_camera"]

        # Setup IK controller
        ik_cfg = DifferentialIKControllerCfg(
            command_type="pose",
            use_relative_mode=False,
            ik_method="dls",
            ik_params={"lambda_val": 0.1},
        )
        self.ik_controller = DifferentialIKController(ik_cfg, num_envs=1, device=self.device)

        # Default gripper orientation (will be updated based on cable direction)
        # For now, just pointing down (180° roll)
        self.default_quat = None  # Will be computed based on cable direction

        # Precompute a fallback orientation (pointing down)
        roll = torch.tensor([math.pi], device=self.device)
        pitch = torch.tensor([0.0], device=self.device)
        yaw = torch.tensor([0.0], device=self.device)
        self.fallback_quat = quat_from_euler_xyz(roll, pitch, yaw)

        # Body/joint names
        self.ee_body_name = "panda_hand"
        self.arm_joint_names = ["panda_joint1", "panda_joint2", "panda_joint3",
                                "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"]

        # Grasp state
        self.grasping = False
        self.grasp_seg_idx = None

        # Indices (resolved after scene is initialized)
        self.ee_body_idx = None
        self.jacobi_body_idx = None
        self.arm_joint_ids = None
        self.gripper_joint_ids = None

        # Resolve indices now (scene already initialized and warmed up)
        self._resolve_indices()

        print("[Tester] Initialized")

    def _resolve_indices(self):
        """Resolve indices after simulation reset."""
        self.ee_body_idx = self.robot_left.find_bodies(self.ee_body_name)[0][0]
        self.jacobi_body_idx = self.ee_body_idx - 1  # Jacobian uses body index - 1
        self.arm_joint_ids = self.robot_left.find_joints(self.arm_joint_names)[0]
        self.gripper_joint_ids = self.robot_left.find_joints(
            ["panda_finger_joint1", "panda_finger_joint2"]
        )[0]
        print(f"[Tester] Resolved: ee_idx={self.ee_body_idx}, arm_joints={self.arm_joint_ids}")

    def step_sim(self, steps: int = 1):
        """Step simulation with optional grasp force."""
        for _ in range(steps):
            if self.grasping:
                self._apply_grasp_force()
            self.scene.write_data_to_sim()
            self.sim.step()
            self.scene.update(self.sim.get_physics_dt())

    def _apply_grasp_force(self):
        """Apply gentle force to keep cable near gripper."""
        # DISABLED: Causes simulation instability (cable becomes NaN)
        return

        if not self.grasping or self.grasp_seg_idx is None:
            return

        body_pos = self.cable.data.body_pos_w[0]
        body_vel = self.cable.data.body_lin_vel_w[0]

        if torch.isnan(body_pos).any():
            return

        # Get EE (fingertip) position
        ee_pos = self.robot_left.data.body_pos_w[:, self.ee_body_idx, :]
        # Fingertip is 10.7cm below panda_hand (minus a bit for grasp)
        fingertip_pos = ee_pos[0].clone()
        fingertip_pos[2] -= (FINGERTIP_OFFSET - 0.02)

        current_pos = body_pos[self.grasp_seg_idx]
        current_vel = body_vel[self.grasp_seg_idx]

        # Gentle PD force (reduced to avoid pushing cable away)
        kp = 5.0
        kd = 1.0
        max_force = 0.5

        error = fingertip_pos - current_pos
        force = kp * error - kd * current_vel

        force_mag = torch.norm(force)
        if force_mag > max_force:
            force = force * (max_force / force_mag)

        num_bodies = body_pos.shape[0]
        forces = torch.zeros((1, num_bodies, 3), device=self.device)
        forces[0, self.grasp_seg_idx] = force
        torques = torch.zeros_like(forces)
        self.cable.set_external_force_and_torque(forces, torques)

    def get_ee_pose(self):
        """Get EE position and quaternion."""
        ee_pos = self.robot_left.data.body_pos_w[:, self.ee_body_idx, :]
        ee_quat = self.robot_left.data.body_quat_w[:, self.ee_body_idx, :]
        return ee_pos, ee_quat

    def compute_ik(self, target_pos, target_quat=None):
        """Compute IK for target position."""
        if target_quat is None:
            target_quat = self.default_quat if self.default_quat is not None else self.fallback_quat

        joint_pos = self.robot_left.data.joint_pos[:, self.arm_joint_ids]
        jacobian = self.robot_left.root_physx_view.get_jacobians()[:, self.jacobi_body_idx, :, self.arm_joint_ids]

        ee_pos_w, ee_quat_w = self.get_ee_pose()
        root_pos_w = self.robot_left.data.root_pos_w
        root_quat_w = self.robot_left.data.root_quat_w

        ee_pos_b, ee_quat_b = subtract_frame_transforms(
            root_pos_w, root_quat_w, ee_pos_w, ee_quat_w
        )
        target_pos_b, target_quat_b = subtract_frame_transforms(
            root_pos_w, root_quat_w, target_pos, target_quat
        )

        command = torch.cat([target_pos_b, target_quat_b], dim=-1)
        self.ik_controller.reset()
        self.ik_controller.set_command(command)

        try:
            result = self.ik_controller.compute(ee_pos_b, ee_quat_b, jacobian, joint_pos)
            return result
        except Exception as e:
            print(f"[IK Warning] {e}")
            return joint_pos

    def move_to_target(self, target_pos, max_steps=100, interp_steps=50):
        """Move to target position with interpolation.

        Args:
            target_pos: Target position
            max_steps: Maximum simulation steps
            interp_steps: Number of steps for interpolation (slower = more steps)
        """
        ee_start, _ = self.get_ee_pose()
        ee_start = ee_start[0].clone()

        for step in range(max_steps):
            t = min(1.0, (step + 1) / interp_steps)
            target_interp = ee_start + t * (target_pos - ee_start)

            new_joint_pos = self.compute_ik(target_interp.unsqueeze(0))

            full_joint_pos = self.robot_left.data.joint_pos.clone()
            full_joint_pos[:, self.arm_joint_ids] = new_joint_pos
            self.robot_left.set_joint_position_target(full_joint_pos)

            self.step_sim(4)

            ee_pos, _ = self.get_ee_pose()
            dist = torch.norm(ee_pos[0] - target_pos).item()
            if dist < 0.01 and t >= 1.0:
                return True

        return False

    def set_gripper(self, position):
        """Set gripper position."""
        full_joint_pos = self.robot_left.data.joint_pos.clone()
        full_joint_pos[:, self.gripper_joint_ids] = position
        self.robot_left.set_joint_position_target(full_joint_pos)

    def create_grasp(self, seg_idx):
        """Create kinematic grasp."""
        self.grasping = True
        self.grasp_seg_idx = seg_idx
        print(f"[Grasp] Created on segment {seg_idx}")

    def release_grasp(self):
        """Release grasp."""
        self.grasping = False
        self.grasp_seg_idx = None
        num_bodies = self.cable.data.body_pos_w.shape[1]
        forces = torch.zeros((1, num_bodies, 3), device=self.device)
        torques = torch.zeros_like(forces)
        self.cable.set_external_force_and_torque(forces, torques)
        print("[Grasp] Released")

    def save_images(self, name):
        """Save camera images."""
        rgb_fl = self.front_left_cam.data.output["rgb"]
        img_fl = rgb_fl[0, ..., :3].cpu().numpy().astype(np.uint8)
        Image.fromarray(img_fl).save(os.path.join(self.output_dir, f"{name}_front_left.png"))

        rgb_oh = self.overhead_cam.data.output["rgb"]
        img_oh = rgb_oh[0, ..., :3].cpu().numpy().astype(np.uint8)
        Image.fromarray(img_oh).save(os.path.join(self.output_dir, f"{name}_overhead.png"))
        print(f"[Images] Saved: {name}")

    def run_test(self):
        """Run grasp test."""
        print("\n" + "=" * 60)
        print("SINGLE ARM GRASP TEST (Modified)")
        print("=" * 60)

        # 1. Settle simulation (already reset in __init__)
        print("\n[Step 1] Settling simulation...")
        self.step_sim(100)

        cable_pos = self.cable.data.body_pos_w[0]
        num_segments = cable_pos.shape[0]
        print(f"  Cable has {num_segments} segments")

        # Get body names to find correct segment index
        body_names = self.cable.body_names
        print(f"  Cable body names: {body_names}")

        # Find segment indices by name
        # Left robot is at Y=-0.30, cable at Y=0.05-0.30
        # We need segment closest to left robot (lowest Y)
        def get_seg_idx_by_name(name):
            for i, n in enumerate(body_names):
                if n == name:
                    return i
            return None

        # Find positions of all segments
        seg_positions = {}
        for i, name in enumerate(body_names):
            seg_positions[name] = cable_pos[i]

        # Find segment with lowest Y (closest to left robot at Y=-0.30)
        min_y = float('inf')
        closest_seg_name = None
        closest_seg_idx = None
        for i, name in enumerate(body_names):
            y = cable_pos[i][1].item()
            if y < min_y:
                min_y = y
                closest_seg_name = name
                closest_seg_idx = i

        # Use the segment closest to the left robot
        grasp_seg_idx = closest_seg_idx
        cable_grasp = cable_pos[grasp_seg_idx].clone()

        # Find next segment for orientation
        # Try to get the next numbered segment
        seg_num = int(closest_seg_name.split('_')[1])
        next_seg_name = f"seg_{seg_num + 1}"
        next_seg_idx = get_seg_idx_by_name(next_seg_name)
        if next_seg_idx is not None:
            cable_next = cable_pos[next_seg_idx].clone()
        else:
            cable_next = cable_grasp.clone()
            cable_next[1] += 0.025  # Assume cable runs along Y

        print(f"  Closest segment to left robot: {closest_seg_name} (idx={grasp_seg_idx})")
        print(f"  Cable grasp target pos: {cable_grasp.cpu().tolist()}")
        print(f"  Cable grasp Y distance from robot: {(cable_grasp[1].item() + 0.30):.3f}m")

        # Store initial cable position for use throughout the test
        # This prevents issues if cable becomes unstable during robot movement
        initial_cable_grasp = cable_grasp.clone()
        initial_cable_next = cable_next.clone()

        ee_pos, ee_quat = self.get_ee_pose()
        print(f"  Left EE pos: {ee_pos[0].cpu().tolist()}")
        print(f"  Left EE quat (wxyz): {ee_quat[0].cpu().tolist()}")

        # Print cable info
        print(f"  Cable joint names: {self.cable.joint_names}")

        # Compute gripper orientation based on cable direction
        print("\n  Computing gripper orientation for cable direction...")
        computed_quat = compute_grasp_quat_for_cable(cable_grasp, cable_next, self.device)
        print(f"  Computed quat (wxyz): {computed_quat[0].cpu().tolist()}")

        # Gripper orientation options:
        # Option A: 180° X only (pointing down, fingers open along Y-axis)
        #   quat = (0, 1, 0, 0) wxyz - fingers open along Y
        # Option B: 180° X + 90° Z (pointing down, fingers open along X-axis)
        #   quat = (0, 0.7071, 0.7071, 0) wxyz - fingers open along X

        # Cable is along Y-axis (front_left image shows cable horizontal)
        # To grasp Y-axis cable, gripper fingers must open along X-axis
        # But image shows fingers parallel to cable -> need different rotation

        # Try: 180° X rotation only (no Z rotation)
        # This makes gripper point down with fingers along Y-axis
        # For Y-axis cable, fingers should open perpendicular (X-axis)
        # So we need 90° Z rotation... but that didn't work

        # Alternative: The cable might be along X-axis (not Y)
        # In that case, we need fingers along Y-axis (no Z rotation)
        quat_no_z = torch.tensor([[0.0, 1.0, 0.0, 0.0]], device=self.device)  # 180° X only
        quat_with_z = torch.tensor([[0.0, 0.7071, 0.7071, 0.0]], device=self.device)  # 180° X + 90° Z

        print(f"  Quat (no Z rot): {quat_no_z[0].cpu().tolist()}")
        print(f"  Quat (90° Z rot): {quat_with_z[0].cpu().tolist()}")

        # Use 90° Z rotation - fingers will open along X-axis
        # Cable is along Y-axis, so fingers need to be perpendicular (X-axis)
        self.default_quat = quat_with_z
        print(f"  Using: 90° Z rotation (fingers along X-axis, perpendicular to Y-axis cable)")

        self.save_images("step1_initial")

        # 2. Move above cable
        print("\n[Step 2] Move above cable...")
        # Use stored initial cable position (prevents NaN issues if cable becomes unstable)
        # panda_hand target = cable_z + approach_height + FINGERTIP_OFFSET
        approach_height = 0.10  # 10cm above cable
        target_above = torch.tensor([
            initial_cable_grasp[0].item(),
            initial_cable_grasp[1].item(),
            initial_cable_grasp[2].item() + approach_height + FINGERTIP_OFFSET
        ], device=self.device)
        print(f"  Target (panda_hand): {target_above.cpu().tolist()}")
        print(f"  Grasp segment: {closest_seg_name} (idx={grasp_seg_idx})")

        self.set_gripper(GRIPPER_OPEN)
        self.move_to_target(target_above, max_steps=150)

        ee_pos, ee_quat = self.get_ee_pose()
        print(f"  Final EE pos: {ee_pos[0].cpu().tolist()}")
        print(f"  Final EE quat (wxyz): {ee_quat[0].cpu().tolist()}")

        # Check cable status after robot movement
        cable_pos_check = self.cable.data.body_pos_w[0]
        if torch.isnan(cable_pos_check).any():
            print(f"  WARNING: Cable became NaN during move! Using stored position.")
            cable_ok = False
        else:
            cable_ok = True
            print(f"  Cable status: OK")

        self.save_images("step2_above")

        # 3. Lower to grasp
        print("\n[Step 3] Lower to grasp...")
        # Use stored initial cable position (safer)
        cable_current = initial_cable_grasp  # Use stored position
        print(f"  Using stored cable position: {cable_current.cpu().tolist()}")

        # Grasp height: position fingertip at cable level
        # FINGERTIP_OFFSET = 0.12m (panda_hand to fingertip, with margin)
        # We want fingertip to be at cable Z level (or slightly below for better contact)
        grasp_clearance = -0.08  # 8cm below cable center for better contact
        target_grasp = torch.tensor([
            cable_current[0].item(),
            cable_current[1].item(),
            cable_current[2].item() + grasp_clearance + FINGERTIP_OFFSET
        ], device=self.device)
        print(f"  Target (panda_hand): {target_grasp.cpu().tolist()}")
        print(f"  Expected fingertip Z: {(cable_current[2].item() + grasp_clearance):.4f}")
        print(f"  Cable Z: {cable_current[2].item():.4f}")

        self.move_to_target(target_grasp, max_steps=100)

        ee_pos, ee_quat = self.get_ee_pose()
        # Use stored position for comparison (current cable might be NaN)
        cable_seg = initial_cable_grasp
        print(f"  Target panda_hand pos: {target_grasp.cpu().tolist()}")
        print(f"  Actual panda_hand pos: {ee_pos[0].cpu().tolist()}")
        print(f"  Position error: {(ee_pos[0] - target_grasp).cpu().tolist()}")
        print(f"  Stored cable pos: {cable_seg.cpu().tolist()}")

        fingertip = ee_pos[0].clone()
        fingertip[2] -= FINGERTIP_OFFSET
        print(f"  Estimated fingertip Z: {fingertip[2].item():.4f}")
        print(f"  Target cable Z: {cable_seg[2].item():.4f}")
        print(f"  Fingertip-Cable Z diff: {(fingertip[2] - cable_seg[2]).item():.4f}m")
        print(f"  XY distance to cable: {torch.norm(fingertip[:2] - cable_seg[:2]).item():.4f}m")
        print(f"  Total distance to cable: {torch.norm(fingertip - cable_seg).item():.4f}m")
        self.save_images("step3_at_grasp")

        # 4. Close gripper
        print("\n[Step 4] Close gripper...")
        self.set_gripper(GRIPPER_CLOSE)
        self.step_sim(100)  # More settling time (was 50)
        self.save_images("step4_closed")

        # 5. Create grasp
        print("\n[Step 5] Create grasp...")
        self.create_grasp(seg_idx=grasp_seg_idx)
        self.step_sim(50)  # More settling time (was 30)
        self.save_images("step5_grasp")

        # 6. Lift
        print("\n[Step 6] Lift cable...")
        # Use stored initial position as "before" reference
        cable_before = initial_cable_grasp.clone()

        # Slower, lower lift to prevent cable slipping
        target_lift = target_grasp.clone()
        target_lift[2] += 0.08  # Reduced from 0.15m to 0.08m
        print(f"  Lift target: {target_lift.cpu().tolist()}")

        # Slow lift with more steps and slower interpolation
        self.move_to_target(target_lift, max_steps=200, interp_steps=150)  # Slower interp
        self.step_sim(50)

        ee_pos, _ = self.get_ee_pose()
        cable_pos_after = self.cable.data.body_pos_w[0]
        cable_after = cable_pos_after[grasp_seg_idx].clone()

        print(f"  Final EE: {ee_pos[0].cpu().tolist()}")
        print(f"  Cable before (stored): {cable_before.cpu().tolist()}")

        if torch.isnan(cable_after).any():
            print(f"  Cable after: NaN (simulation unstable)")
            lifted = False
            lift_amount = 0.0
        else:
            print(f"  Cable after: {cable_after.cpu().tolist()}")
            lifted = cable_after[2].item() > cable_before[2].item() + 0.03
            lift_amount = cable_after[2].item() - cable_before[2].item()

        print(f"\n  === RESULT: Lifted = {lifted}, Amount = {lift_amount:.4f}m ===")

        # Show all segments
        print("\n  All segment Z positions:")
        for i, name in enumerate(body_names):
            pos = cable_pos_after[i]
            if torch.isnan(pos).any():
                print(f"    {name}: NaN!")
            else:
                print(f"    {name}: Z={pos[2].item():.4f}")

        self.save_images("step6_lifted")

        # 7. Release
        print("\n[Step 7] Release...")
        self.release_grasp()
        self.set_gripper(GRIPPER_OPEN)
        self.step_sim(100)
        self.save_images("step7_released")

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print(f"Output: {self.output_dir}")
        print("=" * 60)

        return lifted


def main():
    tester = SimpleGraspTester(args.output_dir)
    success = tester.run_test()
    simulation_app.close()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
