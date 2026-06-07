"""
L字型フック
ケーブルを掛けられる形状
"""
import isaaclab.sim as sim_utils
from isaaclab.assets import RigidObjectCfg

# フックパラメータ
HOOK_VERTICAL_LENGTH = 0.08    # 縦棒 8cm
HOOK_HORIZONTAL_LENGTH = 0.04  # 横棒 4cm
HOOK_RADIUS = 0.005            # 半径 5mm

class HookLShapeCfg:
    """L字型フックの設定"""

    vertical_length: float = HOOK_VERTICAL_LENGTH
    horizontal_length: float = HOOK_HORIZONTAL_LENGTH
    radius: float = HOOK_RADIUS
    color = (0.3, 0.3, 0.3)  # グレー

    @classmethod
    def get_vertical_config(cls) -> RigidObjectCfg:
        """縦棒部分"""
        return RigidObjectCfg(
            prim_path="{ENV_REGEX_NS}/hook_vertical",
            spawn=sim_utils.CylinderCfg(
                radius=cls.radius,
                height=cls.vertical_length,
                axis="Z",
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    kinematic_enabled=True,  # 固定
                ),
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=cls.color,
                ),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=(0.7, 0.0, 0.85 + cls.vertical_length/2),
            ),
        )

    @classmethod
    def get_horizontal_config(cls) -> RigidObjectCfg:
        """横棒部分（ケーブルを掛ける部分）"""
        return RigidObjectCfg(
            prim_path="{ENV_REGEX_NS}/hook_horizontal",
            spawn=sim_utils.CylinderCfg(
                radius=cls.radius,
                height=cls.horizontal_length,
                axis="Y",  # Y軸方向に伸びる
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    kinematic_enabled=True,  # 固定
                ),
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=cls.color,
                ),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=(0.7, 0.0, 0.85 + cls.vertical_length),
            ),
        )


def create_l_hook_usd(stage, prim_path: str):
    """
    L字型フックのUSDを動的に生成
    複合形状として作成
    """
    from pxr import UsdGeom, UsdPhysics, Gf

    # ルートXform
    hook_xform = UsdGeom.Xform.Define(stage, prim_path)

    # 縦棒
    vertical_path = f"{prim_path}/vertical"
    vertical = UsdGeom.Cylinder.Define(stage, vertical_path)
    vertical.GetRadiusAttr().Set(HOOK_RADIUS)
    vertical.GetHeightAttr().Set(HOOK_VERTICAL_LENGTH)
    vertical.GetAxisAttr().Set("Z")

    xform_v = UsdGeom.Xformable(vertical)
    translate_v = xform_v.AddTranslateOp()
    translate_v.Set(Gf.Vec3d(0, 0, HOOK_VERTICAL_LENGTH/2))

    # 横棒
    horizontal_path = f"{prim_path}/horizontal"
    horizontal = UsdGeom.Cylinder.Define(stage, horizontal_path)
    horizontal.GetRadiusAttr().Set(HOOK_RADIUS)
    horizontal.GetHeightAttr().Set(HOOK_HORIZONTAL_LENGTH)
    horizontal.GetAxisAttr().Set("Y")

    xform_h = UsdGeom.Xformable(horizontal)
    translate_h = xform_h.AddTranslateOp()
    translate_h.Set(Gf.Vec3d(0, 0, HOOK_VERTICAL_LENGTH))

    # 物理設定（全体）
    rigid_api = UsdPhysics.RigidBodyAPI.Apply(hook_xform.GetPrim())
    rigid_api.GetKinematicEnabledAttr().Set(True)  # 固定

    # コリジョン
    UsdPhysics.CollisionAPI.Apply(vertical.GetPrim())
    UsdPhysics.CollisionAPI.Apply(horizontal.GetPrim())

    return hook_xform


if __name__ == "__main__":
    print(f"L-Shape Hook Configuration:")
    print(f"  Vertical: {HOOK_VERTICAL_LENGTH*100:.1f} cm")
    print(f"  Horizontal: {HOOK_HORIZONTAL_LENGTH*100:.1f} cm")
    print(f"  Radius: {HOOK_RADIUS*1000:.1f} mm")
