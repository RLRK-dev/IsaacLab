"""
柔軟ケーブル環境の初期状態を可視化
- ロボット2台
- Y字フック
- ケーブル（初期位置）
"""
import numpy as np
import time
from isaaclab.app import AppLauncher

app_launcher = AppLauncher(headless=False)
simulation_app = app_launcher.app

from isaaclab.sim import SimulationContext
from isaaclab.assets import RigidObject, RigidObjectCfg
import isaaclab.sim as sim_utils

def create_y_hook(hook_base_pos):
    """Y字フック"""
    stem_length = 0.08
    stem_radius = 0.008
    arm_length = 0.05
    arm_radius = 0.008
    arm_angle = 45.0
    angle_rad = np.radians(arm_angle)

    stem_cfg = RigidObjectCfg(
        prim_path="/World/YHook/Stem",
        spawn=sim_utils.CylinderCfg(
            radius=stem_radius,
            height=stem_length,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            mass_props=sim_utils.MassPropertiesCfg(mass=0.1),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.4, 0.7, 1.0)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(hook_base_pos[0], hook_base_pos[1], hook_base_pos[2] + stem_length/2),
        ),
    )

    stem_top_z = hook_base_pos[2] + stem_length
    arm_offset_x = (arm_length/2) * np.sin(angle_rad)
    arm_offset_z = (arm_length/2) * np.cos(angle_rad)

    left_arm_cfg = RigidObjectCfg(
        prim_path="/World/YHook/LeftArm",
        spawn=sim_utils.CylinderCfg(
            radius=arm_radius,
            height=arm_length,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            mass_props=sim_utils.MassPropertiesCfg(mass=0.1),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.4, 0.7, 1.0)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(hook_base_pos[0] - arm_offset_x, hook_base_pos[1], stem_top_z + arm_offset_z),
            rot=(0.924, 0.0, 0.383, 0.0),
        ),
    )

    right_arm_cfg = RigidObjectCfg(
        prim_path="/World/YHook/RightArm",
        spawn=sim_utils.CylinderCfg(
            radius=arm_radius,
            height=arm_length,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            mass_props=sim_utils.MassPropertiesCfg(mass=0.1),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.4, 0.7, 1.0)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(hook_base_pos[0] + arm_offset_x, hook_base_pos[1], stem_top_z + arm_offset_z),
            rot=(0.924, 0.0, -0.383, 0.0),
        ),
    )

    stem = RigidObject(stem_cfg)
    left_arm = RigidObject(left_arm_cfg)
    right_arm = RigidObject(right_arm_cfg)

    return stem, left_arm, right_arm


def create_cable_initial(table_z, num_segments=10):
    """
    ケーブルの初期状態（テーブル上に横たわる）
    """
    segment_radius = 0.006
    cable_length = 0.40

    cable_segments = []

    # テーブル上にまっすぐ配置（Y方向に沿って）
    for i in range(num_segments):
        t = i / (num_segments - 1)

        # Y方向に配置
        y = (t - 0.5) * cable_length
        x = 0.3  # フックから離れた位置
        z = table_z + 0.02 + segment_radius  # テーブル上

        seg_cfg = RigidObjectCfg(
            prim_path=f"/World/Cable/Segment_{i}",
            spawn=sim_utils.SphereCfg(
                radius=segment_radius,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
                mass_props=sim_utils.MassPropertiesCfg(mass=0.01),
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.0, 0.5, 0.0)),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(pos=(x, y, z)),
        )

        segment = RigidObject(seg_cfg)
        cable_segments.append(segment)

    return cable_segments


def create_table(pos):
    table_cfg = RigidObjectCfg(
        prim_path="/World/Table",
        spawn=sim_utils.CuboidCfg(
            size=(0.8, 0.8, 0.02),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            mass_props=sim_utils.MassPropertiesCfg(mass=10.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.9, 0.85, 0.75)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(pos=pos),
    )
    return RigidObject(table_cfg)


def create_robot_marker(name, pos, color):
    """ロボット位置のマーカー（簡易表示）"""
    marker_cfg = RigidObjectCfg(
        prim_path=f"/World/{name}",
        spawn=sim_utils.CuboidCfg(
            size=(0.1, 0.1, 0.3),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(pos=pos),
    )
    return RigidObject(marker_cfg)


def main():
    print("=" * 50)
    print("Initial State Visualization")
    print("=" * 50)

    sim_cfg = sim_utils.SimulationCfg(dt=1/60, device="cuda:0")
    sim = SimulationContext(sim_cfg)

    sim.set_camera_view(eye=(1.2, -0.8, 1.0), target=(0.4, 0.0, 0.5))

    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func("/World/Ground", ground_cfg)

    # テーブル
    table_z = 0.4
    table = create_table((0.4, 0.0, table_z))

    # Y字フック
    hook_base_pos = np.array([0.5, 0.0, table_z + 0.01])
    stem, left_arm, right_arm = create_y_hook(hook_base_pos)

    # ケーブル（初期位置：テーブル上）
    cable_segments = create_cable_initial(table_z)

    # ロボット位置マーカー
    left_robot = create_robot_marker("LeftRobot", (0.0, -0.3, table_z + 0.15), (0.2, 0.6, 0.2))
    right_robot = create_robot_marker("RightRobot", (0.0, 0.3, table_z + 0.15), (0.6, 0.2, 0.2))

    sim.reset()

    print("\n" + "=" * 50)
    print("Initial State:")
    print("  - Cable: On table (orange)")
    print("  - Y-Hook: Center of table (blue)")
    print("  - Left Robot: Y = -0.3m (green)")
    print("  - Right Robot: Y = +0.3m (red)")
    print("Press Ctrl+C to exit")
    print("=" * 50)

    while simulation_app.is_running():
        sim.step()
        time.sleep(0.01)


if __name__ == "__main__":
    main()
    simulation_app.close()
