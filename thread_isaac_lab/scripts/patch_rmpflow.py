"""
collect_goal_images.py の DualArmController を RmpFlow ベースに修正するパッチ
"""

# 新しい DualArmController クラスのコード
NEW_CONTROLLER_CODE = '''
# =============================================================================
# Dual Arm Controller (RMPFlow-based)
# =============================================================================

# RMPFlow configuration paths
FRANKA_RMP_CONFIG_DIR = "/home/rlrk/IsaacLab/env_isaaclab/lib/python3.11/site-packages/isaacsim/exts/isaacsim.robot_motion.motion_generation/motion_policy_configs/franka"


class DualArmController:
    """Controller for both arms using RMPFlow with collision avoidance."""

    def __init__(self, scene: InteractiveScene, device: str):
        self.scene = scene
        self.device = device

        self.robot_left = scene["robot_left"]
        self.robot_right = scene["robot_right"]

        # Resolve body and joint indices
        body_ids, _ = self.robot_left.find_bodies("panda_hand")
        self.ee_body_idx = body_ids[0]

        joint_ids, _ = self.robot_left.find_joints("panda_joint.*")
        self.arm_joint_ids = list(joint_ids)
        self.gripper_joint_ids = [7, 8]

        # Default orientation: gripper pointing down (180° around X axis)
        from scipy.spatial.transform import Rotation as R
        final_rot = R.from_euler('x', 180, degrees=True)
        quat_xyzw = final_rot.as_quat()  # scipy returns [x, y, z, w]
        quat_wxyz = [quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]
        print(f"[Controller] Gripper quaternion (wxyz): {quat_wxyz}")
        self.default_quat = torch.tensor([quat_wxyz], device=device)

        # Initialize RMPFlow controllers
        self._init_rmpflow_controllers()

        # Debug: Print initial positions
        print(f"[Controller] Left arm joint pos: {self.robot_left.data.joint_pos[0, :7].cpu().tolist()}")
        print(f"[Controller] Right arm joint pos: {self.robot_right.data.joint_pos[0, :7].cpu().tolist()}")
        left_ee, _ = self.get_ee_pose(self.robot_left)
        right_ee, _ = self.get_ee_pose(self.robot_right)
        print(f"[Controller] Left EE (world): {left_ee[0].cpu().tolist()}")
        print(f"[Controller] Right EE (world): {right_ee[0].cpu().tolist()}")

    def _init_rmpflow_controllers(self):
        """Initialize RMPFlow controllers for both arms."""
        from isaaclab.controllers.rmp_flow import RmpFlowController, RmpFlowControllerCfg

        # RMPFlow configuration
        rmp_cfg = RmpFlowControllerCfg(
            name="rmp_flow",
            config_file=f"{FRANKA_RMP_CONFIG_DIR}/rmpflow/franka_rmpflow_common.yaml",
            urdf_file=f"{FRANKA_RMP_CONFIG_DIR}/lula_franka_gen.urdf",
            collision_file=f"{FRANKA_RMP_CONFIG_DIR}/rmpflow/robot_descriptor.yaml",
            frame_name="panda_hand",
            evaluations_per_frame=4,
        )

        # Create controllers for each arm
        self.left_rmp = RmpFlowController(rmp_cfg, device=self.device)
        self.right_rmp = RmpFlowController(rmp_cfg, device=self.device)

        # Initialize with robot prim paths
        # Note: RmpFlowController needs the actual prim path at runtime
        self.left_rmp.initialize("/World/envs/env_0/Robot_Left/panda")
        self.right_rmp.initialize("/World/envs/env_0/Robot_Right/panda")

        print("[Controller] RMPFlow controllers initialized")

        # Store whether RMPFlow is available
        self.use_rmpflow = True

    def get_ee_pose(self, robot) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get current EE position and quaternion in world frame."""
        ee_pos_w = robot.data.body_pos_w[:, self.ee_body_idx, :]
        ee_quat_w = robot.data.body_quat_w[:, self.ee_body_idx, :]
        return ee_pos_w, ee_quat_w

    def get_fingertip_offset_world(self) -> float:
        """Get the Z offset from panda_hand to fingertip in world frame."""
        return -0.1123  # Fingertip is 10.7cm below panda_hand when pointing down

    def set_targets(
        self,
        left_pos: Optional[torch.Tensor],
        right_pos: Optional[torch.Tensor],
        left_gripper: float,
        right_gripper: float,
        debug: bool = False,
        use_fixed_orientation: bool = False,
    ):
        """Set arm targets and gripper positions using RMPFlow."""

        # Get target orientation
        target_quat = self.default_quat if use_fixed_orientation else None

        # Left arm
        if left_pos is not None:
            left_target = self._compute_rmpflow(
                self.robot_left, self.left_rmp, left_pos, target_quat, debug
            )
        else:
            left_target = self.robot_left.data.joint_pos[:, self.arm_joint_ids]

        # Right arm
        if right_pos is not None:
            right_target = self._compute_rmpflow(
                self.robot_right, self.right_rmp, right_pos, target_quat, debug
            )
        else:
            right_target = self.robot_right.data.joint_pos[:, self.arm_joint_ids]

        # Gripper positions
        left_grip = torch.full((1, 2), left_gripper, device=self.device)
        right_grip = torch.full((1, 2), right_gripper, device=self.device)

        # Set joint position targets
        self.robot_left.set_joint_position_target(torch.cat([left_target, left_grip], dim=-1))
        self.robot_right.set_joint_position_target(torch.cat([right_target, right_grip], dim=-1))

    def _compute_rmpflow(
        self,
        robot,
        rmp_controller,
        target_pos: torch.Tensor,
        target_quat: Optional[torch.Tensor] = None,
        debug: bool = False,
    ) -> torch.Tensor:
        """Compute joint positions using RMPFlow."""

        # Build command tensor: [pos_x, pos_y, pos_z, quat_w, quat_x, quat_y, quat_z]
        if target_quat is None:
            # Use current orientation
            _, current_quat = self.get_ee_pose(robot)
            target_quat = current_quat

        # Command format: [pos(3), quat_wxyz(4)]
        command = torch.cat([target_pos.unsqueeze(0), target_quat], dim=-1)

        # Set command and compute
        rmp_controller.set_command(command)
        joint_pos, joint_vel = rmp_controller.compute()

        if debug:
            current_pos, _ = self.get_ee_pose(robot)
            pos_error = torch.norm(current_pos - target_pos).item()
            print(f"      [RMPFlow Debug] Position error: {pos_error:.4f}m")

        return joint_pos

    def get_gripper_pos(self, robot) -> float:
        """Get current gripper position."""
        return robot.data.joint_pos[:, self.gripper_joint_ids].mean().item()
'''

import re

# 元のファイルを読み込み
input_file = "/home/rlrk/IsaacLab/thread_isaac_lab/scripts/collect_goal_images.py"
with open(input_file, 'r') as f:
    content = f.read()

# より正確なパターン: class DualArmController から class GoalImageCollector の前まで
pattern = r'(class DualArmController:.*?)(class GoalImageCollector:)'

def replacer(m):
    return NEW_CONTROLLER_CODE + '\n\n\n' + m.group(2)

new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)

if new_content != content:
    # 出力ファイルに書き込み
    output_file = "/home/rlrk/IsaacLab/thread_isaac_lab/scripts/collect_goal_images.py"
    with open(output_file, 'w') as f:
        f.write(new_content)

    print("パッチ適用完了")
else:
    print("パターンが見つかりませんでした。手動で確認してください。")
