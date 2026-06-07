#!/usr/bin/env python3
"""
Tight Grip + Incremental Lift Test
- GRIPPER_CLOSE = 0.002 (4mm gap, tighter than 6mm)
- Incremental lift: 0.5mm per step × 300 steps = 15cm
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = True
args.enable_cameras = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS

print("=" * 60)
print("TIGHT GRIP + INCREMENTAL LIFT TEST")
print("GRIPPER_CLOSE = 0.002 (4mm gap)")
print("Lift: 0.5mm/step × 300 steps = 15cm")
print("=" * 60)

# Parameters
GRIPPER_CLOSE = 0.002  # 4mm gap (tighter than 0.003 = 6mm)
FRICTION = 5.0
LIFT_PER_STEP = 0.0005  # 0.5mm per step
LIFT_STEPS = 300  # 300 steps × 0.5mm = 15cm total

# Setup
sim_cfg = sim_utils.SimulationCfg(dt=1/240, render_interval=1)
sim = sim_utils.SimulationContext(sim_cfg)

@configclass
class TestSceneCfg(DualArmSceneCfg):
    contact_left: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
        update_period=0.0, history_length=1, track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"], debug_vis=False,
    )
    contact_right: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
        update_period=0.0, history_length=1, track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"], debug_vis=False,
    )

scene_cfg = TestSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]
contact_left = scene["contact_left"]
contact_right = scene["contact_right"]

device = robot_left.device

# Apply friction
print("\nApplying friction=5.0...")
def set_friction(asset, value):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = value
    materials[..., 1] = value
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, FRICTION)
set_friction(robot_right, FRICTION)
set_friction(cable, FRICTION)

# Setup Diff IK
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=True,
    ik_method="dls",
    ik_params={"lambda_val": 0.1},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

def get_ee_pos(robot, idx):
    return robot.data.body_pos_w[0, idx].cpu().numpy()

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

def get_cable_center_z():
    z_vals = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    valid = z_vals[~np.isnan(z_vals)]
    if len(valid) > 0:
        return np.mean(valid[len(valid)//3:2*len(valid)//3])  # middle third
    return float('nan')

def get_gripper_gap(robot):
    return robot.data.joint_pos[0, -2:].sum().item() * 1000  # mm

# ============================================================
# PHASE 1: OPEN GRIPPERS
# ============================================================
print("\nPhase 1: Open grippers...")
for _ in range(100):
    target = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target[0, -2:] = 0.04
    robot_left.set_joint_position_target(target)
    robot_left.write_data_to_sim()
    target = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target[0, -2:] = 0.04
    robot_right.set_joint_position_target(target)
    robot_right.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

# ============================================================
# PHASE 2A: TELEPORT TO GRASP POSITION
# ============================================================
print("Phase 2A: Teleport to grasp position...")
arm_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
arm_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
arm_left[0, -2:] = 0.04
robot_left.write_joint_state_to_sim(arm_left, robot_left.data.joint_vel[0].unsqueeze(0))

arm_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
arm_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
arm_right[0, -2:] = 0.04
robot_right.write_joint_state_to_sim(arm_right, robot_right.data.joint_vel[0].unsqueeze(0))

for _ in range(50):
    robot_left.set_joint_position_target(arm_left)
    robot_left.write_data_to_sim()
    robot_right.set_joint_position_target(arm_right)
    robot_right.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

# ============================================================
# PHASE 2B: CLOSE GRIPPERS (TIGHT)
# ============================================================
print(f"Phase 2B: Close grippers (GRIPPER_CLOSE={GRIPPER_CLOSE}, target gap={GRIPPER_CLOSE*2*1000}mm)...")

for i in range(300):
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
    target_left[0, -2:] = GRIPPER_CLOSE
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()
    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
    target_right[0, -2:] = GRIPPER_CLOSE
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

# Record Phase 2 state
phase2_ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
phase2_force_l = get_contact_force(contact_left)
phase2_force_r = get_contact_force(contact_right)
phase2_cable_z = get_cable_center_z()
phase2_gap = get_gripper_gap(robot_left)

print(f"\n" + "=" * 60)
print("PHASE 2 COMPLETE")
print("=" * 60)
print(f"  Gap: L={phase2_gap:.2f}mm")
print(f"  Contact Force: L={phase2_force_l:.3f}N, R={phase2_force_r:.3f}N")
print(f"  EE Z: {phase2_ee_z:.4f}")
print(f"  Cable Z: {phase2_cable_z:.4f}")

# ============================================================
# PHASE 3: INCREMENTAL DIFF IK LIFT
# ============================================================
print(f"\n" + "=" * 60)
print("PHASE 3: INCREMENTAL DIFF IK LIFT")
print(f"  Lift per step: {LIFT_PER_STEP*1000}mm")
print(f"  Total steps: {LIFT_STEPS}")
print(f"  Total lift: {LIFT_PER_STEP*LIFT_STEPS*100}cm")
print("=" * 60)

contact_lost_step = None
accumulated_lift = 0.0

print(f"\n  {'Step':>5} | {'EE Z':>7} | {'Lift':>7} | {'Force L':>8} | {'Force R':>8} | {'Cable Z':>8} | {'Gap':>6} | Status")
print("-" * 90)

for i in range(LIFT_STEPS):
    # Reset and set new incremental command each step
    diff_ik_left.reset()
    diff_ik_right.reset()

    # Small incremental lift command
    command = torch.tensor([[0.0, 0.0, LIFT_PER_STEP, 0.0, 0.0, 0.0]], device=device)

    ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left]
    ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left]
    ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right]
    ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right]

    diff_ik_left.set_command(command, ee_pos_left, ee_quat_left)
    diff_ik_right.set_command(command, ee_pos_right, ee_quat_right)

    # Compute and apply IK
    jacobian_left = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
    jacobian_right = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]

    joint_pos_left = robot_left.data.joint_pos[:, :7]
    joint_pos_right = robot_right.data.joint_pos[:, :7]

    joint_cmd_left = diff_ik_left.compute(ee_pos_left, ee_quat_left, jacobian_left, joint_pos_left)
    joint_cmd_right = diff_ik_right.compute(ee_pos_right, ee_quat_right, jacobian_right, joint_pos_right)

    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = joint_cmd_left[0]
    target_left[0, -2:] = GRIPPER_CLOSE
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = joint_cmd_right[0]
    target_right[0, -2:] = GRIPPER_CLOSE
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    accumulated_lift += LIFT_PER_STEP

    # Get current state
    ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)
    cable_z = get_cable_center_z()
    gap = get_gripper_gap(robot_left)
    lift = (ee_z - phase2_ee_z) * 100  # cm

    # Detect contact loss
    status = "OK"
    if contact_lost_step is None and force_l < 1.0 and force_r < 1.0:
        contact_lost_step = i
        status = "*** LOST ***"
    elif contact_lost_step is not None:
        status = "lost"

    # Log every 20 steps or on contact loss
    if i % 20 == 0 or status == "*** LOST ***":
        print(f"  {i:>5} | {ee_z:>7.4f} | {lift:>6.2f}cm | {force_l:>7.3f}N | {force_r:>7.3f}N | {cable_z:>8.4f} | {gap:>5.1f}mm | {status}")

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)

final_ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
final_force_l = get_contact_force(contact_left)
final_force_r = get_contact_force(contact_right)
final_cable_z = get_cable_center_z()
final_gap = get_gripper_gap(robot_left)

print(f"\n1. Phase 2 接触力:")
print(f"   L={phase2_force_l:.3f}N, R={phase2_force_r:.3f}N")
print(f"   Gap: {phase2_gap:.2f}mm")

print(f"\n2. Phase 3 接触喪失:")
if contact_lost_step is not None:
    lost_lift = contact_lost_step * LIFT_PER_STEP * 100  # cm
    print(f"   Step {contact_lost_step} で喪失 (リフト約{lost_lift:.2f}cm時点)")
else:
    print(f"   喪失なし！接触維持成功")

print(f"\n3. Final State:")
print(f"   EE Z: {final_ee_z:.4f} (lift: {(final_ee_z - phase2_ee_z)*100:.2f}cm)")
print(f"   Contact: L={final_force_l:.3f}N, R={final_force_r:.3f}N")
print(f"   Cable Z: {final_cable_z:.4f}")

print(f"\n4. ケーブルZ変化:")
print(f"   Phase 2: {phase2_cable_z:.4f}")
print(f"   Phase 3: {final_cable_z:.4f}")
if not np.isnan(final_cable_z) and not np.isnan(phase2_cable_z):
    cable_lift = (final_cable_z - phase2_cable_z) * 100
    print(f"   上昇量: {cable_lift:.2f}cm")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"| 項目 | Phase 2 | Phase 3 Final |")
print(f"|------|---------|---------------|")
print(f"| Gap (mm) | {phase2_gap:.2f} | {final_gap:.2f} |")
print(f"| Force L (N) | {phase2_force_l:.3f} | {final_force_l:.3f} |")
print(f"| Force R (N) | {phase2_force_r:.3f} | {final_force_r:.3f} |")
print(f"| EE Z | {phase2_ee_z:.4f} | {final_ee_z:.4f} |")
print(f"| Cable Z | {phase2_cable_z:.4f} | {final_cable_z:.4f} |")

if contact_lost_step is None:
    print(f"\n✅ SUCCESS: 接触を維持しながら{(final_ee_z - phase2_ee_z)*100:.1f}cmリフト完了！")
else:
    print(f"\n❌ FAILED: Step {contact_lost_step}で接触喪失")

simulation_app.close()
