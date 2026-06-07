"""
柔軟ケーブル（セグメント分割版）
複数のカプセルをSphericalJointで連結
"""
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, RigidObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg

# ケーブルパラメータ
NUM_SEGMENTS = 20          # セグメント数
SEGMENT_LENGTH = 0.03      # 各セグメント長さ (3cm)
SEGMENT_RADIUS = 0.006     # 半径 (6mm)
TOTAL_LENGTH = NUM_SEGMENTS * SEGMENT_LENGTH  # 30cm
SEGMENT_MASS = 0.003       # 各セグメント質量 (3g)

def create_flexible_cable_usd(stage, prim_path: str, num_segments: int = NUM_SEGMENTS):
    """
    柔軟ケーブルのUSDを動的に生成
    """
    from pxr import UsdGeom, UsdPhysics, Gf, Sdf

    # ルートXform
    cable_xform = UsdGeom.Xform.Define(stage, prim_path)

    prev_prim_path = None

    for i in range(num_segments):
        seg_path = f"{prim_path}/segment_{i:02d}"

        # カプセル形状
        capsule = UsdGeom.Capsule.Define(stage, seg_path)
        capsule.GetRadiusAttr().Set(SEGMENT_RADIUS)
        capsule.GetHeightAttr().Set(SEGMENT_LENGTH)
        capsule.GetAxisAttr().Set("X")  # X軸方向

        # 位置設定
        xform = UsdGeom.Xformable(capsule)
        translate_op = xform.AddTranslateOp()
        x_pos = i * SEGMENT_LENGTH
        translate_op.Set(Gf.Vec3d(x_pos, 0, 0))

        # 剛体物理
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(capsule.GetPrim())
        mass_api = UsdPhysics.MassAPI.Apply(capsule.GetPrim())
        mass_api.GetMassAttr().Set(SEGMENT_MASS)

        # コリジョン
        collision_api = UsdPhysics.CollisionAPI.Apply(capsule.GetPrim())

        # ジョイント（2番目以降のセグメント）
        if prev_prim_path is not None:
            joint_path = f"{prim_path}/joint_{i-1:02d}_{i:02d}"
            joint = UsdPhysics.SphericalJoint.Define(stage, joint_path)

            # 接続するボディを設定
            joint.GetBody0Rel().SetTargets([Sdf.Path(prev_prim_path)])
            joint.GetBody1Rel().SetTargets([Sdf.Path(seg_path)])

            # ジョイント位置（前セグメントの端）
            joint.GetLocalPos0Attr().Set(Gf.Vec3f(SEGMENT_LENGTH/2, 0, 0))
            joint.GetLocalPos1Attr().Set(Gf.Vec3f(-SEGMENT_LENGTH/2, 0, 0))

            # 回転制限（柔軟性の調整）
            joint.GetConeAngle0LimitAttr().Set(30.0)  # 30度まで曲がる
            joint.GetConeAngle1LimitAttr().Set(30.0)

        prev_prim_path = seg_path

    return cable_xform


class FlexibleCableCfg:
    """柔軟ケーブルの設定"""

    num_segments: int = NUM_SEGMENTS
    segment_length: float = SEGMENT_LENGTH
    segment_radius: float = SEGMENT_RADIUS
    segment_mass: float = SEGMENT_MASS
    total_length: float = TOTAL_LENGTH

    # 色
    color = (1.0, 0.4, 0.0)  # オレンジ

    # 物理パラメータ
    joint_stiffness: float = 0.1   # ジョイント剛性（低い=柔軟）
    joint_damping: float = 0.05    # ジョイント減衰

    @classmethod
    def get_config(cls) -> ArticulationCfg:
        """ArticulationCfgを返す"""
        return ArticulationCfg(
            prim_path="{ENV_REGEX_NS}/cable",
            spawn=sim_utils.UsdFileCfg(
                usd_path="generated://flexible_cable",
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    disable_gravity=False,
                    linear_damping=0.1,
                    angular_damping=0.1,
                ),
                articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                    enabled_self_collisions=False,
                ),
            ),
            init_state=ArticulationCfg.InitialStateCfg(
                pos=(0.5, 0.0, 0.85),  # テーブル上
            ),
            actuators={
                "cable_joints": ImplicitActuatorCfg(
                    joint_names_expr=["joint_.*"],
                    stiffness=cls.joint_stiffness,
                    damping=cls.joint_damping,
                ),
            },
        )


# 簡易版: RigidObjectのリストとして実装
def create_cable_segments_config():
    """
    複数のRigidObjectとして柔軟ケーブルを実装
    """
    segments = {}

    for i in range(NUM_SEGMENTS):
        seg_name = f"cable_seg_{i:02d}"
        x_pos = 0.5 + i * SEGMENT_LENGTH  # テーブル中心から

        segments[seg_name] = RigidObjectCfg(
            prim_path=f"{{ENV_REGEX_NS}}/{seg_name}",
            spawn=sim_utils.CapsuleCfg(
                radius=SEGMENT_RADIUS,
                height=SEGMENT_LENGTH,
                axis="X",
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    disable_gravity=False,
                    linear_damping=0.5,
                    angular_damping=0.5,
                ),
                mass_props=sim_utils.MassPropertiesCfg(mass=SEGMENT_MASS),
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(1.0, 0.4, 0.0),  # オレンジ
                ),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=(x_pos, 0.0, 0.85),
            ),
        )

    return segments


if __name__ == "__main__":
    print(f"Flexible Cable Configuration:")
    print(f"  Segments: {NUM_SEGMENTS}")
    print(f"  Segment length: {SEGMENT_LENGTH*100:.1f} cm")
    print(f"  Total length: {TOTAL_LENGTH*100:.1f} cm")
    print(f"  Radius: {SEGMENT_RADIUS*1000:.1f} mm")
    print(f"  Total mass: {NUM_SEGMENTS * SEGMENT_MASS * 1000:.1f} g")
