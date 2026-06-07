"""test_diffik_minimal.py — DiffIK pose mode minimal verification.

Single left Franka (wall-mounted), overhead + front cameras for video.
DiffIK(dls, pose) moves EE down 10mm with downward orientation constraint.
N_SIM_PER_IK=4: each IK computation followed by 4 sim.step() for PD tracking.
Max 100 IK steps (= 400 sim steps). Converge threshold: 1mm pos + 5deg ori.

Arm PD: FRANKA_PANDA_HIGH_PD_CFG (stiffness=400, damping=80, disable_gravity=True).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time

import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=str, default="cuda:0")
parser.add_argument("--headless", action="store_true", default=False)
parser.add_argument("--record_video", action="store_true", default=False)
parser.add_argument("--output_dir", type=str, default="data/test_diffik_minimal")
parser.add_argument("--side", type=str, default="left", choices=["left", "right"])
args, _ = parser.parse_known_args()

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=args.headless, device=args.device,
                           enable_cameras=True)
sim_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.sensors import CameraCfg
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
N_SIM_PER_IK = 4  # sim.step() per IK computation
# Hand pointing down (-Z) — (w, x, y, z) format
HAND_DOWN_QUAT_WXYZ = (0.0, 0.7071, 0.7071, 0.0)


# Select arm config based on --side
if args.side == "left":
    _ROBOT_BASE = ROBOT_LEFT_BASE
    _INIT_JOINTS = CLIP_APPROACH_LEFT_JOINTS
    _ROBOT_PRIM = "{ENV_REGEX_NS}/Robot_Left"
else:
    _ROBOT_BASE = ROBOT_RIGHT_BASE
    _INIT_JOINTS = CLIP_APPROACH_RIGHT_JOINTS
    _ROBOT_PRIM = "{ENV_REGEX_NS}/Robot_Right"


@configclass
class MinimalFrankaCfg(ArticulationCfg):
    """Single Franka — HIGH_PD_CFG gains, disable_gravity=True."""

    prim_path: str = _ROBOT_PRIM

    spawn: sim_utils.UrdfFileCfg = sim_utils.UrdfFileCfg(
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

    init_state: ArticulationCfg.InitialStateCfg = ArticulationCfg.InitialStateCfg(
        pos=_ROBOT_BASE,
        rot=ROBOT_BASE_QUAT_WXYZ,
        joint_pos={
            "panda_joint1": _INIT_JOINTS[0],
            "panda_joint2": _INIT_JOINTS[1],
            "panda_joint3": _INIT_JOINTS[2],
            "panda_joint4": _INIT_JOINTS[3],
            "panda_joint5": _INIT_JOINTS[4],
            "panda_joint6": _INIT_JOINTS[5],
            "panda_joint7": _INIT_JOINTS[6],
            "panda_finger_joint.*": 0.04,
        },
        joint_vel={".*": 0.0},
    )

    actuators: dict = {
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


@configclass
class MinimalSceneCfg(InteractiveSceneCfg):
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

    robot: MinimalFrankaCfg = MinimalFrankaCfg()

    # Overhead camera — top-down view of arm
    overhead_camera: CameraCfg = CameraCfg(
        prim_path="{ENV_REGEX_NS}/OverheadCamera",
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=9.0,
            horizontal_aperture=25.0,
            clipping_range=(0.1, 10.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.40, -0.09, 1.3),
            rot=(0.7071, 0.0, 0.7071, 0.0),  # look -Z (down)
            convention="world",
        ),
        width=640, height=480,
        data_types=["rgb"], update_period=0.0,
    )

    # Front camera — side view to see Z descent
    front_camera: CameraCfg = CameraCfg(
        prim_path="{ENV_REGEX_NS}/FrontCamera",
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=18.0,
            horizontal_aperture=25.0,
            clipping_range=(0.1, 10.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.80, -0.09, 0.80),
            rot=(0.0, 0.0, 0.0, 1.0),  # look -X
            convention="world",
        ),
        width=640, height=480,
        data_types=["rgb"], update_period=0.0,
    )


def capture_frame(scene, frames_dir, frame_idx, cam_names=("overhead_camera", "front_camera")):
    """Capture one frame from each camera."""
    from PIL import Image
    for name in cam_names:
        try:
            cam = scene[name]
            cam.update(dt=0.0)
            rgb = cam.data.output["rgb"][0].cpu().numpy()
            if rgb.shape[-1] == 4:
                rgb = rgb[:, :, :3]
            d = os.path.join(frames_dir, name)
            os.makedirs(d, exist_ok=True)
            Image.fromarray(rgb.astype(np.uint8)).save(
                os.path.join(d, f"frame_{frame_idx:06d}.png"))
        except Exception as e:
            if frame_idx == 0:
                print(f"  [VIDEO] Capture error ({name}): {e}")


def encode_videos(frames_dir, output_dir, n_frames, fps=30):
    """Encode frames to MP4."""
    paths = []
    for name in ("overhead_camera", "front_camera"):
        d = os.path.join(frames_dir, name)
        if not os.path.isdir(d):
            continue
        out = os.path.join(output_dir, f"diffik_minimal_{name}.mp4")
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", os.path.join(d, "frame_%06d.png"),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p", out,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            sz = os.path.getsize(out) / (1024 * 1024)
            print(f"  [VIDEO] {out} ({sz:.1f} MB, {n_frames} frames)")
            paths.append(out)
        else:
            print(f"  [VIDEO] ffmpeg error ({name}): {r.stderr[:200]}")
    # Cleanup frames
    shutil.rmtree(frames_dir, ignore_errors=True)
    return paths


def main():
    device = f"cuda:{app_launcher.device_id}"
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    frames_dir = os.path.join(output_dir, "_frames")

    print(f"[MINIMAL] side={args.side}, device={device}")
    print(f"[MINIMAL] N_SIM_PER_IK={N_SIM_PER_IK}")
    print(f"[MINIMAL] init_joints={list(_INIT_JOINTS)}")
    print(f"[MINIMAL] record_video={args.record_video}")

    scene_cfg = MinimalSceneCfg(num_envs=1, env_spacing=5.0)
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
    scene = InteractiveScene(scene_cfg)

    sim.reset()
    scene.reset()

    robot = scene["robot"]

    # Write init joints + PD sync
    robot.write_joint_state_to_sim(
        robot.data.default_joint_pos, robot.data.default_joint_vel
    )
    robot.set_joint_position_target(robot.data.default_joint_pos)
    robot.write_data_to_sim()  # Send PD targets to PhysX

    # PD stabilization
    for _ in range(50):
        sim.step()
        scene.update(sim.cfg.dt)
    print("[MINIMAL] PD stabilized (50 steps)")

    # Find hand body index
    hbl = robot.find_bodies("panda_hand")[0][0]
    jbl = hbl - 1
    print(f"[MINIMAL] hand_body={hbl}, jac_body={jbl}")

    # Read init EE position
    ee_init = robot.data.body_pos_w[0, hbl, :3].clone()
    print(f"[MINIMAL] Init EE: ({ee_init[0]:.6f}, {ee_init[1]:.6f}, {ee_init[2]:.6f})")

    # [CHECK] EE Z > TABLE_HEIGHT
    assert ee_init[2].item() > TABLE_HEIGHT, (
        f"SAFETY: EE Z={ee_init[2]:.4f} < TABLE_HEIGHT={TABLE_HEIGHT}"
    )
    print(f"[MINIMAL] CHECK OK: EE Z={ee_init[2]:.4f} > TABLE={TABLE_HEIGHT}")

    # Target: 10mm below current EE, with downward orientation
    target_pos = ee_init.clone().unsqueeze(0)  # (1, 3)
    target_pos[0, 2] -= 0.01  # -10mm

    target_quat = torch.tensor([HAND_DOWN_QUAT_WXYZ], dtype=torch.float32, device=device)  # (1,4) wxyz

    assert target_pos[0, 2].item() > TABLE_HEIGHT, (
        f"SAFETY: target Z={target_pos[0,2]:.4f} < TABLE_HEIGHT={TABLE_HEIGHT}"
    )
    print(f"[MINIMAL] Target EE: ({target_pos[0,0]:.6f}, {target_pos[0,1]:.6f}, {target_pos[0,2]:.6f})")
    print(f"[MINIMAL] Target quat (wxyz): {HAND_DOWN_QUAT_WXYZ}")
    print(f"[MINIMAL] CHECK OK: target Z={target_pos[0,2]:.4f} > TABLE={TABLE_HEIGHT}")

    # Read init EE orientation for comparison
    ee_init_quat = robot.data.body_quat_w[0, hbl].clone()
    print(f"[MINIMAL] Init EE quat (wxyz): ({ee_init_quat[0]:.4f}, {ee_init_quat[1]:.4f}, "
          f"{ee_init_quat[2]:.4f}, {ee_init_quat[3]:.4f})")

    # Create DiffIK controller — POSE mode (7DOF: position + orientation)
    ik_cfg = DifferentialIKControllerCfg(
        command_type="pose",
        use_relative_mode=False,
        ik_method="dls",
        ik_params={"lambda_val": 0.01},
    )
    ik_ctrl = DifferentialIKController(ik_cfg, num_envs=1, device=device)

    print(f"\n[MINIMAL] === DiffIK POSE mode: Z descent 10mm + downward ori (N_SIM_PER_IK={N_SIM_PER_IK}) ===")
    print(f"{'ik_step':>7} | {'EE_X':>10} {'EE_Y':>10} {'EE_Z':>10} | {'pos_mm':>8} {'ori_deg':>8} | "
          f"{'max_jdelta':>12} {'PD_track':>10} | {'dX_mm':>7} {'dY_mm':>7} {'dZ_mm':>7}")
    print("-" * 120)

    converged = False
    frame_idx = 0
    start_time = time.time()
    step_log = []

    def _quat_angle_deg(q1, q2):
        """Angle between two quaternions (wxyz) in degrees."""
        dot = (q1 * q2).sum().abs().clamp(max=1.0)
        return 2.0 * torch.acos(dot).item() * 180.0 / 3.14159265

    for ik_step in range(100):
        # EE pose in world frame
        ee_pose_w = robot.data.body_pose_w[:, hbl]
        root_pose_w = robot.data.root_pose_w

        # Convert EE to body frame
        ee_pos_b, ee_quat_b = subtract_frame_transforms(
            root_pose_w[:, 0:3], root_pose_w[:, 3:7],
            ee_pose_w[:, 0:3], ee_pose_w[:, 3:7],
        )

        # Convert target (pos + quat) to body frame
        tgt_pos_b, tgt_quat_b = subtract_frame_transforms(
            root_pose_w[:, 0:3], root_pose_w[:, 3:7],
            target_pos, target_quat,
        )

        # Pose mode command: (pos_b, quat_b) concatenated → (1, 7)
        ik_ctrl.set_command(
            torch.cat([tgt_pos_b, tgt_quat_b], dim=-1),
            ee_pos=ee_pos_b, ee_quat=ee_quat_b,
        )

        # Jacobian in body frame
        jacobian = robot.root_physx_view.get_jacobians()[:, jbl, :, ARM_JOINT_IDS]
        base_rot = root_pose_w[:, 3:7]
        base_rot_matrix = matrix_from_quat(quat_inv(base_rot))
        jacobian[:, :3, :] = torch.bmm(base_rot_matrix, jacobian[:, :3, :])
        jacobian[:, 3:, :] = torch.bmm(base_rot_matrix, jacobian[:, 3:, :])

        joint_pos = robot.data.joint_pos[:, ARM_JOINT_IDS]
        joint_pos_des = ik_ctrl.compute(ee_pos_b, ee_quat_b, jacobian, joint_pos)

        # Diagnostics before apply
        delta = (joint_pos_des[0] - joint_pos[0]).abs().max().item()

        # Apply joint target once, then sim.step() N_SIM_PER_IK times
        tgt = robot.data.joint_pos.clone()
        tgt[0, :7] = joint_pos_des[0]
        robot.set_joint_position_target(tgt)
        robot.write_data_to_sim()

        for sub in range(N_SIM_PER_IK):
            sim.step()
            scene.update(sim.cfg.dt)
            if args.record_video:
                capture_frame(scene, frames_dir, frame_idx)
                frame_idx += 1

        # After N_SIM_PER_IK sim.steps — measure EE pos + ori error
        ee_now = robot.data.body_pos_w[0, hbl, :3]
        ee_quat_now = robot.data.body_quat_w[0, hbl]
        pos_err_mm = torch.norm(ee_now - target_pos[0]).item() * 1000
        ori_err_deg = _quat_angle_deg(ee_quat_now, target_quat[0])
        pd_track = (joint_pos_des[0] - robot.data.joint_pos[0, :7]).abs().max().item()
        dx_mm = (ee_now[0] - ee_init[0]).item() * 1000
        dy_mm = (ee_now[1] - ee_init[1]).item() * 1000
        dz_mm = (ee_now[2] - ee_init[2]).item() * 1000

        print(f"{ik_step:7d} | {ee_now[0]:10.6f} {ee_now[1]:10.6f} {ee_now[2]:10.6f} | "
              f"{pos_err_mm:8.3f} {ori_err_deg:8.3f} | {delta:12.6f} {pd_track:10.6f} | "
              f"{dx_mm:7.2f} {dy_mm:7.2f} {dz_mm:7.2f}")

        step_log.append({
            "ik_step": ik_step,
            "ee": [round(ee_now[0].item(), 6), round(ee_now[1].item(), 6), round(ee_now[2].item(), 6)],
            "pos_err_mm": round(pos_err_mm, 3),
            "ori_err_deg": round(ori_err_deg, 3),
            "pd_track": round(pd_track, 6),
            "dx_mm": round(dx_mm, 2),
            "dy_mm": round(dy_mm, 2),
            "dz_mm": round(dz_mm, 2),
        })

        if pos_err_mm < 1.0 and ori_err_deg < 5.0:
            print(f"\n[MINIMAL] CONVERGED at ik_step {ik_step} "
                  f"(sim_steps={ik_step * N_SIM_PER_IK + N_SIM_PER_IK}): "
                  f"pos={pos_err_mm:.3f}mm, ori={ori_err_deg:.3f}deg")
            converged = True
            break

    elapsed = time.time() - start_time

    if not converged:
        ee_final = robot.data.body_pos_w[0, hbl, :3]
        ee_quat_final = robot.data.body_quat_w[0, hbl]
        pos_err_final = torch.norm(ee_final - target_pos[0]).item() * 1000
        ori_err_final = _quat_angle_deg(ee_quat_final, target_quat[0])
        print(f"\n[MINIMAL] NOT CONVERGED after 100 IK steps ({100*N_SIM_PER_IK} sim steps): "
              f"pos={pos_err_final:.3f}mm, ori={ori_err_final:.3f}deg")

    # Final state
    ee_final = robot.data.body_pos_w[0, hbl, :3]
    ee_quat_final = robot.data.body_quat_w[0, hbl]
    dx = (ee_final[0] - ee_init[0]).item() * 1000
    dy = (ee_final[1] - ee_init[1]).item() * 1000
    dz = (ee_final[2] - ee_init[2]).item() * 1000
    pos_err_final = torch.norm(ee_final - target_pos[0]).item() * 1000
    ori_err_final = _quat_angle_deg(ee_quat_final, target_quat[0])

    print(f"\n[MINIMAL] Final EE: ({ee_final[0]:.6f}, {ee_final[1]:.6f}, {ee_final[2]:.6f})")
    print(f"[MINIMAL] Final quat: ({ee_quat_final[0]:.4f}, {ee_quat_final[1]:.4f}, "
          f"{ee_quat_final[2]:.4f}, {ee_quat_final[3]:.4f})")
    print(f"[MINIMAL] Init→Final: dX={dx:.2f}mm dY={dy:.2f}mm dZ={dz:.2f}mm (target dZ=-10.00mm)")
    print(f"[MINIMAL] Final pos error: {pos_err_final:.3f}mm, ori error: {ori_err_final:.3f}deg")
    print(f"[MINIMAL] Elapsed: {elapsed:.1f}s")

    # Encode video
    video_paths = []
    if args.record_video and frame_idx > 0:
        video_paths = encode_videos(frames_dir, output_dir, frame_idx)

    # Save RUN_METRICS.json
    metrics = {
        "test": f"diffik_minimal_pose_z10mm_{args.side}",
        "side": args.side,
        "command_type": "pose",
        "n_sim_per_ik": N_SIM_PER_IK,
        "pd_gains": {"stiffness": 400.0, "damping": 80.0},
        "disable_gravity": True,
        "target_quat_wxyz": list(HAND_DOWN_QUAT_WXYZ),
        "init_ee": [round(ee_init[0].item(), 6), round(ee_init[1].item(), 6), round(ee_init[2].item(), 6)],
        "init_quat_wxyz": [round(ee_init_quat[i].item(), 6) for i in range(4)],
        "target_ee": [round(target_pos[0, 0].item(), 6), round(target_pos[0, 1].item(), 6), round(target_pos[0, 2].item(), 6)],
        "final_ee": [round(ee_final[0].item(), 6), round(ee_final[1].item(), 6), round(ee_final[2].item(), 6)],
        "final_quat_wxyz": [round(ee_quat_final[i].item(), 6) for i in range(4)],
        "final_pos_err_mm": round(pos_err_final, 3),
        "final_ori_err_deg": round(ori_err_final, 3),
        "drift_mm": {"dX": round(dx, 2), "dY": round(dy, 2), "dZ": round(dz, 2)},
        "converged": converged,
        "converge_step": step_log[-1]["ik_step"] if converged else None,
        "total_sim_steps": (step_log[-1]["ik_step"] + 1) * N_SIM_PER_IK if step_log else 0,
        "elapsed_s": round(elapsed, 1),
        "video_paths": video_paths,
        "pass": converged and abs(dx) < 1.0 and abs(dy) < 1.0 and ori_err_final < 5.0,
        "step_log": step_log,
    }

    metrics_path = os.path.join(output_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[MINIMAL] Metrics saved: {metrics_path}")


if __name__ == "__main__":
    main()
    sim_app.close()
