"""
D6 Joint Grasp Manager
======================

D6 Joint (Configurable Joint) を使用した拘束ベース把持の実装。
摩擦把持が機能しない場合の代替手段として使用。

D6 Jointは全6自由度（3並進 + 3回転）を個別に制御できるジョイント。
全自由度をロックすることで、グリッパーとケーブルを固定接続できる。

使用方法:
    from thread_isaac_lab.utils.d6_grasp_manager import D6GraspManager

    # 初期化
    grasp_manager = D6GraspManager()

    # シーン作成後に参照設定
    grasp_manager.set_stage(stage)

    # 把持作成（グリッパーフィンガーとケーブルセグメントを接続）
    grasp_manager.create_grasp(
        "left",
        gripper_prim_path="/World/envs/env_0/Robot_Left/panda_leftfinger",
        cable_prim_path="/World/envs/env_0/Cable/seg_0"
    )

    # 把持解除
    grasp_manager.release_grasp("left")

Author: THREAD Research Team
"""

from typing import Optional, Dict, Tuple
import torch


class D6GraspManager:
    """D6 Joint（拘束ベース）による把持管理。

    D6 Jointを動的に作成・削除してグリッパーとオブジェクトを固定接続する。
    力ベースの把持（KinematicGraspManager）より安定した把持が可能。
    """

    def __init__(self):
        """初期化。"""
        self._stage = None
        self._device = "cuda:0"

        # 把持状態
        self._left_joint_path: Optional[str] = None
        self._right_joint_path: Optional[str] = None
        self._left_grasping: bool = False
        self._right_grasping: bool = False

        # 把持時のオフセット（ワールド座標系）
        self._left_local_pos0 = None
        self._left_local_pos1 = None
        self._right_local_pos0 = None
        self._right_local_pos1 = None

        print("[D6GraspManager] Initialized")

    def set_stage(self, stage):
        """USDステージを設定。

        Args:
            stage: pxr.Usd.Stage オブジェクト
        """
        self._stage = stage
        print("[D6GraspManager] Stage set")

    def set_device(self, device: str):
        """デバイスを設定。

        Args:
            device: "cuda:0" or "cpu"
        """
        self._device = device

    @property
    def left_grasping(self) -> bool:
        """左手が把持中かどうか。"""
        return self._left_grasping

    @property
    def right_grasping(self) -> bool:
        """右手が把持中かどうか。"""
        return self._right_grasping

    def create_grasp(
        self,
        side: str,
        gripper_prim_path: str,
        cable_prim_path: str,
        local_pos0: Optional[Tuple[float, float, float]] = None,
        local_pos1: Optional[Tuple[float, float, float]] = None,
    ) -> bool:
        """D6 Jointで把持を作成。

        Args:
            side: "left" or "right"
            gripper_prim_path: グリッパーのUSDパス（例: /World/envs/env_0/Robot_Left/panda_leftfinger）
            cable_prim_path: ケーブルセグメントのUSDパス（例: /World/envs/env_0/Cable/seg_0）
            local_pos0: gripper側のローカルオフセット（デフォルト: (0, 0, 0)）
            local_pos1: cable側のローカルオフセット（デフォルト: (0, 0, 0)）

        Returns:
            True if successful
        """
        if self._stage is None:
            print("[D6GraspManager] Error: Stage not set!")
            return False

        # pxrモジュールのインポート（Isaac Sim環境でのみ利用可能）
        try:
            from pxr import Usd, UsdPhysics, Gf, Sdf, PhysxSchema
        except ImportError:
            print("[D6GraspManager] Error: pxr module not available!")
            return False

        # 既存の把持を解除
        if side == "left" and self._left_grasping:
            self.release_grasp("left")
        elif side == "right" and self._right_grasping:
            self.release_grasp("right")

        # ジョイントパスを生成
        joint_path = f"/World/envs/env_0/GraspJoint_{side}"
        if side == "left":
            self._left_joint_path = joint_path
        else:
            self._right_joint_path = joint_path

        # Primが存在するか確認
        gripper_prim = self._stage.GetPrimAtPath(gripper_prim_path)
        cable_prim = self._stage.GetPrimAtPath(cable_prim_path)

        if not gripper_prim.IsValid():
            print(f"[D6GraspManager] Error: Gripper prim not found: {gripper_prim_path}")
            return False
        if not cable_prim.IsValid():
            print(f"[D6GraspManager] Error: Cable prim not found: {cable_prim_path}")
            return False

        # D6 Jointを作成
        # 注意: UsdPhysics.Joint はFixedJointの基底クラス
        # D6Jointを直接作成するには、FixedJointを使用して全自由度をロック
        joint = UsdPhysics.FixedJoint.Define(self._stage, joint_path)

        # body0とbody1を接続
        joint.GetBody0Rel().SetTargets([Sdf.Path(gripper_prim_path)])
        joint.GetBody1Rel().SetTargets([Sdf.Path(cable_prim_path)])

        # ローカル位置を設定
        pos0 = local_pos0 if local_pos0 else (0.0, 0.0, 0.0)
        pos1 = local_pos1 if local_pos1 else (0.0, 0.0, 0.0)

        joint.GetLocalPos0Attr().Set(Gf.Vec3f(*pos0))
        joint.GetLocalPos1Attr().Set(Gf.Vec3f(*pos1))

        # ローカル回転（単位クォータニオン = 回転なし）
        joint.GetLocalRot0Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        joint.GetLocalRot1Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))

        # PhysX APIを適用し、break forceを無効化（無限大）
        # Note: BreakForce/BreakTorque attributes may not be available in all Isaac Sim versions
        try:
            physx_joint = PhysxSchema.PhysxJointAPI.Apply(joint.GetPrim())
            # Disable joint breaking by setting very high values
            # PhysX uses FLT_MAX (~3.4e38) for "unbreakable", but 1e10 is practically infinite
            joint_prim = joint.GetPrim()
            # Try to set break force/torque if attributes exist
            if joint_prim.HasAttribute("physxJoint:breakForce"):
                joint_prim.GetAttribute("physxJoint:breakForce").Set(1e10)
            else:
                joint_prim.CreateAttribute("physxJoint:breakForce", Sdf.ValueTypeNames.Float).Set(1e10)
            if joint_prim.HasAttribute("physxJoint:breakTorque"):
                joint_prim.GetAttribute("physxJoint:breakTorque").Set(1e10)
            else:
                joint_prim.CreateAttribute("physxJoint:breakTorque", Sdf.ValueTypeNames.Float).Set(1e10)
            print(f"[D6GraspManager] Set break force/torque to 1e10 (practically unbreakable)")
        except Exception as e:
            print(f"[D6GraspManager] Warning: Could not apply PhysxJointAPI or set break force: {e}")

        # 把持状態を更新
        if side == "left":
            self._left_grasping = True
            self._left_local_pos0 = pos0
            self._left_local_pos1 = pos1
        else:
            self._right_grasping = True
            self._right_local_pos0 = pos0
            self._right_local_pos1 = pos1

        print(f"[D6GraspManager] Created {side} grasp: {gripper_prim_path} <-> {cable_prim_path}")
        return True

    def create_d6_joint_grasp(
        self,
        side: str,
        gripper_prim_path: str,
        cable_prim_path: str,
        lock_all_axes: bool = True,
    ) -> bool:
        """D6 Joint（Configurable Joint）で把持を作成。

        D6 Jointは全6自由度を個別に制御できる。
        - lock_all_axes=True: 全自由度をロック（FixedJointと同等）
        - lock_all_axes=False: 一部の自由度を許可（柔軟な接続）

        Args:
            side: "left" or "right"
            gripper_prim_path: グリッパーのUSDパス
            cable_prim_path: ケーブルセグメントのUSDパス
            lock_all_axes: 全自由度をロックするか

        Returns:
            True if successful
        """
        if self._stage is None:
            print("[D6GraspManager] Error: Stage not set!")
            return False

        try:
            from pxr import Usd, UsdPhysics, Gf, Sdf, PhysxSchema
        except ImportError:
            print("[D6GraspManager] Error: pxr module not available!")
            return False

        # 既存の把持を解除
        if side == "left" and self._left_grasping:
            self.release_grasp("left")
        elif side == "right" and self._right_grasping:
            self.release_grasp("right")

        joint_path = f"/World/envs/env_0/D6GraspJoint_{side}"

        # Primが存在するか確認
        gripper_prim = self._stage.GetPrimAtPath(gripper_prim_path)
        cable_prim = self._stage.GetPrimAtPath(cable_prim_path)

        if not gripper_prim.IsValid() or not cable_prim.IsValid():
            print(f"[D6GraspManager] Error: Prim not found")
            return False

        # PhysicsJointを作成し、LimitAPIを適用してD6 Joint化
        joint_prim = self._stage.DefinePrim(joint_path, "PhysicsJoint")

        # body0とbody1の関係を設定
        joint_prim.CreateRelationship("physics:body0").SetTargets([Sdf.Path(gripper_prim_path)])
        joint_prim.CreateRelationship("physics:body1").SetTargets([Sdf.Path(cable_prim_path)])

        # ローカル位置と回転を設定
        joint_prim.CreateAttribute("physics:localPos0", Sdf.ValueTypeNames.Point3f).Set(Gf.Vec3f(0, 0, 0))
        joint_prim.CreateAttribute("physics:localPos1", Sdf.ValueTypeNames.Point3f).Set(Gf.Vec3f(0, 0, 0))
        joint_prim.CreateAttribute("physics:localRot0", Sdf.ValueTypeNames.Quatf).Set(Gf.Quatf(1, 0, 0, 0))
        joint_prim.CreateAttribute("physics:localRot1", Sdf.ValueTypeNames.Quatf).Set(Gf.Quatf(1, 0, 0, 0))

        if lock_all_axes:
            # 全軸にLimitAPIを適用してロック
            for axis in ["transX", "transY", "transZ", "rotX", "rotY", "rotZ"]:
                limit_api = UsdPhysics.LimitAPI.Apply(joint_prim, axis)
                limit_api.GetLowAttr().Set(0.0)
                limit_api.GetHighAttr().Set(0.0)

        # PhysX API
        PhysxSchema.PhysxJointAPI.Apply(joint_prim)

        # 状態更新
        if side == "left":
            self._left_joint_path = joint_path
            self._left_grasping = True
        else:
            self._right_joint_path = joint_path
            self._right_grasping = True

        print(f"[D6GraspManager] Created D6 joint {side} grasp")
        return True

    def release_grasp(self, side: str) -> bool:
        """把持を解除。

        Args:
            side: "left" or "right"

        Returns:
            True if successful
        """
        if self._stage is None:
            return False

        joint_path = self._left_joint_path if side == "left" else self._right_joint_path

        if joint_path is None:
            print(f"[D6GraspManager] No {side} grasp to release")
            return False

        # ジョイントPrimを削除
        joint_prim = self._stage.GetPrimAtPath(joint_path)
        if joint_prim.IsValid():
            self._stage.RemovePrim(joint_path)
            print(f"[D6GraspManager] Released {side} grasp")

        # 状態をリセット
        if side == "left":
            self._left_joint_path = None
            self._left_grasping = False
            self._left_local_pos0 = None
            self._left_local_pos1 = None
        else:
            self._right_joint_path = None
            self._right_grasping = False
            self._right_local_pos0 = None
            self._right_local_pos1 = None

        return True

    def release_all(self):
        """全ての把持を解除。"""
        self.release_grasp("left")
        self.release_grasp("right")

    def is_grasping(self, side: str) -> bool:
        """把持中かどうかを確認。

        Args:
            side: "left" or "right"

        Returns:
            True if grasping
        """
        return self._left_grasping if side == "left" else self._right_grasping

    def update(self):
        """毎フレーム更新（D6 Jointでは不要だが、互換性のために実装）。

        KinematicGraspManagerとのAPI互換性のため。
        D6 Jointはシミュレーションが自動的に拘束を維持するので、
        外部からの更新は不要。
        """
        pass  # D6 Jointは自動的に拘束を維持

    def set_references(self, cable, controller):
        """互換性のためのダミーメソッド。

        KinematicGraspManagerとの互換性を維持。
        D6GraspManagerでは使用しない。
        """
        pass


def get_grasp_prim_paths(env_idx: int = 0) -> Dict[str, Dict[str, str]]:
    """把持に使用するPrimパスを取得。

    Args:
        env_idx: 環境インデックス

    Returns:
        Dict with gripper and cable paths for each side
    """
    return {
        "left": {
            "gripper": f"/World/envs/env_{env_idx}/Robot_Left/panda_leftfinger",
            "cable_seg_0": f"/World/envs/env_{env_idx}/Cable/seg_0",
            "cable_seg_9": f"/World/envs/env_{env_idx}/Cable/seg_9",
        },
        "right": {
            "gripper": f"/World/envs/env_{env_idx}/Robot_Right/panda_leftfinger",
            "cable_seg_0": f"/World/envs/env_{env_idx}/Cable/seg_0",
            "cable_seg_9": f"/World/envs/env_{env_idx}/Cable/seg_9",
        },
    }


# =============================================================================
# 使用例
# =============================================================================

"""
使用例:

```python
from isaaclab.app import AppLauncher
# ... AppLauncher setup ...

import isaaclab.sim as sim_utils
from thread_isaac_lab.utils.d6_grasp_manager import D6GraspManager, get_grasp_prim_paths

# シーン作成後
stage = sim_utils.get_current_stage()

# D6GraspManager初期化
grasp_manager = D6GraspManager()
grasp_manager.set_stage(stage)

# Primパスを取得
paths = get_grasp_prim_paths(env_idx=0)

# 把持を作成（左グリッパーでケーブルseg_0を把持）
grasp_manager.create_grasp(
    "left",
    gripper_prim_path=paths["left"]["gripper"],
    cable_prim_path=paths["left"]["cable_seg_0"],
)

# シミュレーション実行
for _ in range(100):
    sim.step()
    # grasp_manager.update() は不要（D6 Jointが自動維持）

# 把持解除
grasp_manager.release_grasp("left")
```

注意事項:
1. D6 Jointはシミュレーションが自動的に拘束を維持
2. 把持作成はsim.step()の間に行う（step直後が最適）
3. 大きな外力が加わるとジョイントが破断する可能性あり（BreakForce設定）
4. マルチ環境では各環境ごとにジョイントパスを変更する必要あり
"""
