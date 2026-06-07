"""
双腕ロボット + 柔軟ケーブル環境設定
"""
from __future__ import annotations

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import CameraCfg
from isaaclab.utils import configclass
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

# ケーブルパラメータ
NUM_CABLE_SEGMENTS = 20
CABLE_SEGMENT_LENGTH = 0.03  # 3cm
CABLE_SEGMENT_RADIUS = 0.006  # 6mm
CABLE_TOTAL_LENGTH = NUM_CABLE_SEGMENTS * CABLE_SEGMENT_LENGTH  # 60cm

# テーブルパラメータ
TABLE_HEIGHT = 0.75  # 75cm（標準作業台高さ）
TABLE_SIZE = (0.8, 1.0, 0.03)  # 80cm x 100cm x 3cm

# ロボット配置
ROBOT_DISTANCE_FROM_TABLE = 0.15  # テーブル端から15cm
ROBOT_SEPARATION = 0.6  # ロボット間距離 60cm

# Franka USD path
FRANKA_PANDA_USD = f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd"


@configclass
class DualArmFlexCableSceneCfg(InteractiveSceneCfg):
    """柔軟ケーブル + 双腕ロボットのシーン設定"""

    num_envs: int = 1
    env_spacing: float = 3.0

    # 地面
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    # ライト
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(intensity=1500.0, color=(1.0, 1.0, 1.0)),
    )

    # テーブル
    table = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/table",
        spawn=sim_utils.CuboidCfg(
            size=TABLE_SIZE,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.7, 0.6, 0.5)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.5, 0.0, TABLE_HEIGHT - TABLE_SIZE[2]/2),
        ),
    )

    # 左ロボット（テーブルの左側）
    robot_left = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/robot_left",
        spawn=sim_utils.UsdFileCfg(
            usd_path=FRANKA_PANDA_USD,
            activate_contact_sensors=True,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                max_depenetration_velocity=5.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=0,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.5 - TABLE_SIZE[0]/2 - ROBOT_DISTANCE_FROM_TABLE, -ROBOT_SEPARATION/2, 0.4),
            rot=(0.707, 0.0, 0.0, 0.707),  # 90度回転してテーブルに向ける
            joint_pos={
                "panda_joint1": 0.0,
                "panda_joint2": -0.569,
                "panda_joint3": 0.0,
                "panda_joint4": -2.810,
                "panda_joint5": 0.0,
                "panda_joint6": 3.037,
                "panda_joint7": 0.741,
                "panda_finger_joint1": 0.04,
                "panda_finger_joint2": 0.04,
            },
        ),
        actuators={
            "panda_shoulder": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[1-4]"],
                effort_limit_sim=87.0,
                stiffness=80.0,
                damping=4.0,
            ),
            "panda_forearm": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[5-7]"],
                effort_limit_sim=12.0,
                stiffness=80.0,
                damping=4.0,
            ),
            "panda_hand": ImplicitActuatorCfg(
                joint_names_expr=["panda_finger_joint.*"],
                effort_limit_sim=200.0,
                stiffness=2e3,
                damping=1e2,
            ),
        },
    )

    # 右ロボット（テーブルの右側）
    robot_right = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/robot_right",
        spawn=sim_utils.UsdFileCfg(
            usd_path=FRANKA_PANDA_USD,
            activate_contact_sensors=True,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                max_depenetration_velocity=5.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=0,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.5 - TABLE_SIZE[0]/2 - ROBOT_DISTANCE_FROM_TABLE, ROBOT_SEPARATION/2, 0.4),
            rot=(0.707, 0.0, 0.0, 0.707),  # 90度回転してテーブルに向ける
            joint_pos={
                "panda_joint1": 0.0,
                "panda_joint2": -0.569,
                "panda_joint3": 0.0,
                "panda_joint4": -2.810,
                "panda_joint5": 0.0,
                "panda_joint6": 3.037,
                "panda_joint7": 0.741,
                "panda_finger_joint1": 0.04,
                "panda_finger_joint2": 0.04,
            },
        ),
        actuators={
            "panda_shoulder": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[1-4]"],
                effort_limit_sim=87.0,
                stiffness=80.0,
                damping=4.0,
            ),
            "panda_forearm": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[5-7]"],
                effort_limit_sim=12.0,
                stiffness=80.0,
                damping=4.0,
            ),
            "panda_hand": ImplicitActuatorCfg(
                joint_names_expr=["panda_finger_joint.*"],
                effort_limit_sim=200.0,
                stiffness=2e3,
                damping=1e2,
            ),
        },
    )

    # L字フック（縦棒）
    hook_vertical = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/hook_vertical",
        spawn=sim_utils.CylinderCfg(
            radius=0.008,
            height=0.10,
            axis="Z",
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.2, 0.2, 0.7)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.7, 0.0, TABLE_HEIGHT + 0.05),
        ),
    )

    # L字フック（横棒）
    hook_horizontal = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/hook_horizontal",
        spawn=sim_utils.CylinderCfg(
            radius=0.008,
            height=0.05,
            axis="Y",
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.2, 0.2, 0.7)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.7, 0.0, TABLE_HEIGHT + 0.10),
        ),
    )

    # 左ハンドカメラ
    left_hand_camera = CameraCfg(
        prim_path="{ENV_REGEX_NS}/robot_left/panda_hand/left_camera",
        update_period=0.1,
        height=320,
        width=320,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=24.0,
            focus_distance=0.4,
            horizontal_aperture=20.955,
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.05, 0.0, 0.05),
            rot=(0.707, 0.0, 0.707, 0.0),
            convention="ros",
        ),
    )

    # 右ハンドカメラ
    right_hand_camera = CameraCfg(
        prim_path="{ENV_REGEX_NS}/robot_right/panda_hand/right_camera",
        update_period=0.1,
        height=320,
        width=320,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=24.0,
            focus_distance=0.4,
            horizontal_aperture=20.955,
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.05, 0.0, 0.05),
            rot=(0.707, 0.0, 0.707, 0.0),
            convention="ros",
        ),
    )

    # 俯瞰カメラ
    overhead_camera = CameraCfg(
        prim_path="{ENV_REGEX_NS}/overhead_camera",
        update_period=0.1,
        height=480,
        width=640,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=24.0,
            focus_distance=1.5,
            horizontal_aperture=20.955,
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.5, 0.0, 1.8),
            rot=(0.0, 0.707, 0.0, 0.707),  # 下向き
            convention="ros",
        ),
    )


# task_state次元（柔軟ケーブル対応）
# セグメント位置: 20 * 3 = 60D
# フック位置: 3D
# 左EE位置: 3D
# 右EE位置: 3D
# 距離: 5D (cable_center_hook, left_ee_cable, right_ee_cable, left_ee_hook, right_ee_hook)
TASK_STATE_DIM = 60 + 3 + 3 + 3 + 5  # = 74D


if __name__ == "__main__":
    print(f"Flexible Cable Environment Configuration")
    print(f"  Cable segments: {NUM_CABLE_SEGMENTS}")
    print(f"  Cable length: {CABLE_TOTAL_LENGTH*100:.0f} cm")
    print(f"  Table height: {TABLE_HEIGHT*100:.0f} cm")
    print(f"  Task state dim: {TASK_STATE_DIM}D")
