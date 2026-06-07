# Copyright (c) 2024-2025, THREAD Project
# SPDX-License-Identifier: BSD-3-Clause
"""Dual Arm Skill Reward Calculator - 双腕スキル別報酬計算."""

from __future__ import annotations

import torch
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DualArmObservation:
    """双腕観測データの構造化表現."""

    # 左腕
    left_joint_pos: torch.Tensor  # (num_envs, 9)
    left_joint_vel: torch.Tensor  # (num_envs, 9)
    left_ee_pos: torch.Tensor     # (num_envs, 3)

    # 右腕
    right_joint_pos: torch.Tensor  # (num_envs, 9)
    right_joint_vel: torch.Tensor  # (num_envs, 9)
    right_ee_pos: torch.Tensor     # (num_envs, 3)

    # オブジェクト（従来: 単一点）
    cable_pos: torch.Tensor  # (num_envs, 3) - 後方互換性のため維持
    hook_pos: torch.Tensor   # (num_envs, 3)

    # ケーブルセグメント（10セグメント × 3D = 30D）
    cable_segments: Optional[torch.Tensor] = None  # (num_envs, 10, 3)
    cable_left_end: Optional[torch.Tensor] = None  # (num_envs, 3) - segment 0
    cable_right_end: Optional[torch.Tensor] = None  # (num_envs, 3) - segment 9
    cable_center: Optional[torch.Tensor] = None    # (num_envs, 3) - segment 4-5 average

    # 相対位置（オプション）
    left_ee_to_cable: Optional[torch.Tensor] = None   # (num_envs, 3)
    right_ee_to_cable: Optional[torch.Tensor] = None  # (num_envs, 3)
    cable_to_hook: Optional[torch.Tensor] = None      # (num_envs, 3)

    @classmethod
    def from_flat_tensor(cls, obs: torch.Tensor) -> "DualArmObservation":
        """60次元のフラットテンソルからDualArmObservationを構築.

        観測空間レイアウト (60D):
        - [0:9]   Left joint positions
        - [9:18]  Left joint velocities
        - [18:21] Left EE position
        - [21:30] Right joint positions
        - [30:39] Right joint velocities
        - [39:42] Right EE position
        - [42:45] Cable position
        - [45:48] Hook position
        - [48:51] Left EE to Cable relative
        - [51:54] Right EE to Cable relative
        - [54:57] Cable to Hook relative
        - [57:60] Additional info (unused)
        """
        return cls(
            left_joint_pos=obs[:, 0:9],
            left_joint_vel=obs[:, 9:18],
            left_ee_pos=obs[:, 18:21],
            right_joint_pos=obs[:, 21:30],
            right_joint_vel=obs[:, 30:39],
            right_ee_pos=obs[:, 39:42],
            cable_pos=obs[:, 42:45],
            hook_pos=obs[:, 45:48],
            left_ee_to_cable=obs[:, 48:51] if obs.shape[1] > 48 else None,
            right_ee_to_cable=obs[:, 51:54] if obs.shape[1] > 51 else None,
            cable_to_hook=obs[:, 54:57] if obs.shape[1] > 54 else None,
        )

    @classmethod
    def from_task_state(
        cls,
        task_state: torch.Tensor,
        proprio: Optional[torch.Tensor] = None,
    ) -> "DualArmObservation":
        """44次元のtask_stateからDualArmObservationを構築.

        Task State レイアウト (44D):
        - [0:30]  Cable segment positions (10 segments × 3D)
        - [30:33] Hook position
        - [33:36] Left EE position
        - [36:39] Right EE position
        - [39:40] Cable-Hook distance
        - [40:41] Left EE-Cable distance
        - [41:42] Right EE-Cable distance
        - [42:43] Left EE-Hook distance
        - [43:44] Right EE-Hook distance

        Proprio レイアウト (34D):
        - [0:7]   Left joint positions
        - [7:14]  Left joint velocities
        - [14:15] Left gripper
        - [15:22] Right joint positions
        - [22:29] Right joint velocities
        - [29:30] Right gripper
        - [30:34] Base (unused)
        """
        num_envs = task_state.shape[0]
        device = task_state.device

        # ケーブルセグメント抽出 (10 segments × 3D)
        cable_segments = task_state[:, :30].reshape(num_envs, 10, 3)
        cable_left_end = cable_segments[:, 0]      # 左端 (segment 0)
        cable_right_end = cable_segments[:, 9]     # 右端 (segment 9)
        cable_center = cable_segments[:, 4:6].mean(dim=1)  # 中央 (segments 4-5平均)
        cable_pos = cable_center  # 後方互換性: 中央点をcable_posとして使用

        # フックとEE位置
        hook_pos = task_state[:, 30:33]
        left_ee_pos = task_state[:, 33:36]
        right_ee_pos = task_state[:, 36:39]

        # Proprioceptionから関節情報を抽出
        if proprio is not None:
            left_joint_pos = proprio[:, 0:7]
            left_joint_vel = proprio[:, 7:14]
            right_joint_pos = proprio[:, 15:22]
            right_joint_vel = proprio[:, 22:29]
        else:
            # Proprioが無い場合はゼロで初期化
            left_joint_pos = torch.zeros(num_envs, 9, device=device)
            left_joint_vel = torch.zeros(num_envs, 9, device=device)
            right_joint_pos = torch.zeros(num_envs, 9, device=device)
            right_joint_vel = torch.zeros(num_envs, 9, device=device)

        return cls(
            left_joint_pos=left_joint_pos,
            left_joint_vel=left_joint_vel,
            left_ee_pos=left_ee_pos,
            right_joint_pos=right_joint_pos,
            right_joint_vel=right_joint_vel,
            right_ee_pos=right_ee_pos,
            cable_pos=cable_pos,
            hook_pos=hook_pos,
            cable_segments=cable_segments,
            cable_left_end=cable_left_end,
            cable_right_end=cable_right_end,
            cable_center=cable_center,
        )


class DualArmSkillRewardCalculator:
    """双腕スキル別報酬計算器.

    各スキルに対して専用の報酬関数を提供し、
    スキル訓練時に適切な学習信号を与える。
    """

    def __init__(
        self,
        device: str = "cuda",
        # 距離報酬スケール
        distance_scale: float = 1.0,
        # 協調報酬重み
        coordination_weight: float = 0.1,
        # グリッパー報酬重み
        gripper_weight: float = 0.5,
        # 速度ペナルティ重み
        velocity_penalty_weight: float = 0.01,
        # アクションペナルティ重み
        action_penalty_weight: float = 0.001,
    ):
        self.device = device
        self.distance_scale = distance_scale
        self.coordination_weight = coordination_weight
        self.gripper_weight = gripper_weight
        self.velocity_penalty_weight = velocity_penalty_weight
        self.action_penalty_weight = action_penalty_weight

        # スキル別報酬関数のマッピング
        self.skill_reward_functions = {
            "bimanual_reach": self._compute_reach_reward,
            "bimanual_grasp": self._compute_grasp_reward,
            "bimanual_lift": self._compute_lift_reward,
            "bimanual_transport": self._compute_transport_reward,
            "bimanual_hang": self._compute_hang_reward,
            "bimanual_release": self._compute_release_reward,
        }

    def compute_skill_reward(
        self,
        skill_name: str,
        obs: torch.Tensor,
        action: torch.Tensor,
        next_obs: torch.Tensor,
        gripper_state: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """スキル別報酬を計算.

        Args:
            skill_name: スキル名
            obs: 現在の観測 (num_envs, 60)
            action: 実行されたアクション (num_envs, 18)
            next_obs: 次の観測 (num_envs, 60)
            gripper_state: グリッパー状態（オプション）

        Returns:
            reward: スキル報酬 (num_envs,)
            info: 報酬の内訳辞書
        """
        if skill_name not in self.skill_reward_functions:
            raise ValueError(f"Unknown skill: {skill_name}")

        # 観測をパース
        current_obs = DualArmObservation.from_flat_tensor(obs)
        next_obs_parsed = DualArmObservation.from_flat_tensor(next_obs)

        # スキル固有報酬を計算
        reward, info = self.skill_reward_functions[skill_name](
            current_obs, next_obs_parsed, action, gripper_state
        )

        # 共通ペナルティを追加
        velocity_penalty = self._compute_velocity_penalty(current_obs)
        action_penalty = self._compute_action_penalty(action)

        reward = reward - velocity_penalty - action_penalty
        info["velocity_penalty"] = velocity_penalty
        info["action_penalty"] = action_penalty

        return reward, info

    # =====================================================
    # スキル別報酬関数
    # =====================================================

    def _compute_reach_reward(
        self,
        obs: DualArmObservation,
        next_obs: DualArmObservation,
        action: torch.Tensor,
        gripper_state: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """Bimanual Reach スキルの報酬.

        目標: 左手をケーブル左端(segment 0)、右手をケーブル右端(segment 9)に近づける
        """
        num_envs = obs.left_ee_pos.shape[0]

        # ケーブル端点を取得（cable_segmentsがある場合は使用）
        if obs.cable_left_end is not None and obs.cable_right_end is not None:
            left_target = obs.cable_left_end    # segment 0
            right_target = obs.cable_right_end  # segment 9
            next_left_target = next_obs.cable_left_end
            next_right_target = next_obs.cable_right_end
        else:
            # フォールバック: 従来の単一点
            left_target = obs.cable_pos
            right_target = obs.cable_pos
            next_left_target = next_obs.cable_pos
            next_right_target = next_obs.cable_pos

        # 現在の距離（各手が対応する端点へ）
        left_dist = torch.norm(obs.left_ee_pos - left_target, dim=-1)
        right_dist = torch.norm(obs.right_ee_pos - right_target, dim=-1)

        # 次ステップの距離
        next_left_dist = torch.norm(next_obs.left_ee_pos - next_left_target, dim=-1)
        next_right_dist = torch.norm(next_obs.right_ee_pos - next_right_target, dim=-1)

        # 距離改善報酬（近づいたら正）
        left_improvement = (left_dist - next_left_dist) * self.distance_scale
        right_improvement = (right_dist - next_right_dist) * self.distance_scale

        # 絶対距離報酬（近いほど高い）
        left_proximity = torch.exp(-left_dist * 5.0)
        right_proximity = torch.exp(-right_dist * 5.0)

        # 両腕の協調報酬（同じくらいの距離を維持）
        dist_diff = torch.abs(left_dist - right_dist)
        coordination_reward = torch.exp(-dist_diff * 3.0) * self.coordination_weight

        # スキル成功ボーナス（両方が閾値以内）
        success_threshold = 0.08
        success_bonus = torch.where(
            (next_left_dist < success_threshold) & (next_right_dist < success_threshold),
            torch.ones(num_envs, device=self.device) * 10.0,
            torch.zeros(num_envs, device=self.device)
        )

        # 総報酬
        reward = (
            left_improvement + right_improvement +
            left_proximity + right_proximity +
            coordination_reward + success_bonus
        )

        info = {
            "left_dist": left_dist,
            "right_dist": right_dist,
            "left_improvement": left_improvement,
            "right_improvement": right_improvement,
            "coordination_reward": coordination_reward,
            "success_bonus": success_bonus,
            "skill_success": (next_left_dist < success_threshold) & (next_right_dist < success_threshold),
        }

        return reward, info

    def _compute_grasp_reward(
        self,
        obs: DualArmObservation,
        next_obs: DualArmObservation,
        action: torch.Tensor,
        gripper_state: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """Bimanual Grasp スキルの報酬.

        目標: 左手でケーブル左端(segment 0)、右手でケーブル右端(segment 9)を把持
        """
        num_envs = obs.left_ee_pos.shape[0]

        # ケーブル端点を取得
        if obs.cable_left_end is not None and obs.cable_right_end is not None:
            left_target = obs.cable_left_end    # segment 0 - 左端
            right_target = obs.cable_right_end  # segment 9 - 右端
        else:
            # フォールバック: 従来の単一点
            left_target = obs.cable_pos
            right_target = obs.cable_pos

        # EE位置がケーブル端点に近いことを確認
        left_dist = torch.norm(obs.left_ee_pos - left_target, dim=-1)
        right_dist = torch.norm(obs.right_ee_pos - right_target, dim=-1)

        # 近接報酬
        proximity_reward = torch.exp(-left_dist * 10.0) + torch.exp(-right_dist * 10.0)

        # グリッパーアクション報酬（閉じる方向に）
        # アクション [0:9] = 左腕、[9:18] = 右腕
        # 最後の2つがグリッパー: [7:9] = 左グリッパー、[16:18] = 右グリッパー
        left_gripper_action = action[:, 7:9].mean(dim=-1)  # 平均
        right_gripper_action = action[:, 16:18].mean(dim=-1)

        # 近くにいるときだけグリッパーを閉じる（独立した判定）
        left_close = left_dist < 0.05
        right_close = right_dist < 0.05

        # 各手が近い時にのみグリッパーを閉じる報酬
        left_gripper_reward = torch.where(
            left_close,
            -left_gripper_action * self.gripper_weight,  # 負の値=閉じる
            torch.zeros(num_envs, device=self.device)
        )
        right_gripper_reward = torch.where(
            right_close,
            -right_gripper_action * self.gripper_weight,
            torch.zeros(num_envs, device=self.device)
        )
        gripper_reward = left_gripper_reward + right_gripper_reward

        # グリッパー同期報酬（両方が同時に閉じる）
        gripper_sync = torch.exp(-torch.abs(left_gripper_action - right_gripper_action) * 2.0)

        # 把持成功ボーナス
        grasp_threshold = 0.03
        if gripper_state is not None:
            grasp_success = gripper_state[:, 0] & gripper_state[:, 1]  # 両方が把持中
            success_bonus = torch.where(
                grasp_success,
                torch.ones(num_envs, device=self.device) * 20.0,
                torch.zeros(num_envs, device=self.device)
            )
        else:
            # グリッパー状態がない場合は距離ベースで推定
            # 両端をそれぞれ把持
            both_grasped = (left_dist < grasp_threshold) & (right_dist < grasp_threshold)
            success_bonus = torch.where(
                both_grasped,
                torch.ones(num_envs, device=self.device) * 10.0,
                torch.zeros(num_envs, device=self.device)
            )

        reward = proximity_reward + gripper_reward + gripper_sync * 0.5 + success_bonus

        info = {
            "left_dist": left_dist,
            "right_dist": right_dist,
            "proximity_reward": proximity_reward,
            "gripper_reward": gripper_reward,
            "gripper_sync": gripper_sync,
            "success_bonus": success_bonus,
            "skill_success": (left_dist < grasp_threshold) & (right_dist < grasp_threshold),
        }

        return reward, info

    def _compute_lift_reward(
        self,
        obs: DualArmObservation,
        next_obs: DualArmObservation,
        action: torch.Tensor,
        gripper_state: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """Bimanual Lift スキルの報酬.

        目標: 両端を把持したままケーブルを持ち上げる（中央のZ軸上昇）
        """
        num_envs = obs.left_ee_pos.shape[0]

        # ケーブル端点と中央を取得
        if obs.cable_left_end is not None and obs.cable_center is not None:
            left_target = obs.cable_left_end
            right_target = obs.cable_right_end
            cable_center = obs.cable_center
            next_cable_center = next_obs.cable_center
        else:
            left_target = obs.cable_pos
            right_target = obs.cable_pos
            cable_center = obs.cable_pos
            next_cable_center = next_obs.cable_pos

        # ケーブル中央の高さ変化
        cable_z = cable_center[:, 2]
        next_cable_z = next_cable_center[:, 2]
        lift_progress = (next_cable_z - cable_z) * 10.0  # 上昇に報酬

        # EEとケーブル端点の距離維持（把持を維持）
        left_dist = torch.norm(obs.left_ee_pos - left_target, dim=-1)
        right_dist = torch.norm(obs.right_ee_pos - right_target, dim=-1)

        # 把持維持報酬
        maintain_grasp = torch.exp(-left_dist * 10.0) + torch.exp(-right_dist * 10.0)

        # 両腕の高さを揃える
        left_z = obs.left_ee_pos[:, 2]
        right_z = obs.right_ee_pos[:, 2]
        height_sync = torch.exp(-torch.abs(left_z - right_z) * 5.0) * self.coordination_weight

        # ケーブルがU字形状になることを促進（両端より中央が低い）
        # 持ち上げ中は両端が上、中央がやや下がU字形状
        if obs.cable_left_end is not None:
            left_end_z = obs.cable_left_end[:, 2]
            right_end_z = obs.cable_right_end[:, 2]
            avg_end_z = (left_end_z + right_end_z) / 2
            # 両端の平均高さが中央より高いとボーナス（U字形状）
            u_shape_reward = torch.clamp(avg_end_z - cable_z, min=0) * 2.0
        else:
            u_shape_reward = torch.zeros(num_envs, device=self.device)

        # 目標高さボーナス（中央がフック高さより上）
        target_height = 0.9  # ターゲット高さ
        height_bonus = torch.where(
            next_cable_z > target_height,
            torch.ones(num_envs, device=self.device) * 10.0,
            torch.zeros(num_envs, device=self.device)
        )

        reward = lift_progress + maintain_grasp + height_sync + u_shape_reward + height_bonus

        info = {
            "cable_height": cable_z,
            "lift_progress": lift_progress,
            "maintain_grasp": maintain_grasp,
            "height_sync": height_sync,
            "u_shape_reward": u_shape_reward,
            "height_bonus": height_bonus,
            "skill_success": next_cable_z > target_height,
        }

        return reward, info

    def _compute_transport_reward(
        self,
        obs: DualArmObservation,
        next_obs: DualArmObservation,
        action: torch.Tensor,
        gripper_state: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """Bimanual Transport スキルの報酬.

        目標: ケーブル中央(segments 4-5)をフック位置まで運ぶ
        """
        num_envs = obs.left_ee_pos.shape[0]

        # ケーブル端点と中央を取得
        if obs.cable_center is not None:
            cable_center = obs.cable_center
            next_cable_center = next_obs.cable_center
            left_target = obs.cable_left_end
            right_target = obs.cable_right_end
        else:
            cable_center = obs.cable_pos
            next_cable_center = next_obs.cable_pos
            left_target = obs.cable_pos
            right_target = obs.cable_pos

        # ケーブル中央とフックの距離
        cable_hook_dist = torch.norm(cable_center - obs.hook_pos, dim=-1)
        next_cable_hook_dist = torch.norm(next_cable_center - next_obs.hook_pos, dim=-1)

        # 距離改善報酬
        transport_progress = (cable_hook_dist - next_cable_hook_dist) * self.distance_scale * 5.0

        # 近接報酬
        proximity_reward = torch.exp(-cable_hook_dist * 3.0)

        # EEとケーブル端点の距離維持（把持を維持）
        left_dist = torch.norm(obs.left_ee_pos - left_target, dim=-1)
        right_dist = torch.norm(obs.right_ee_pos - right_target, dim=-1)
        maintain_grasp = torch.exp(-left_dist * 10.0) + torch.exp(-right_dist * 10.0)

        # ケーブル中央がフック上方にあることを確認（Z軸）
        cable_above_hook = cable_center[:, 2] > obs.hook_pos[:, 2]
        height_reward = torch.where(
            cable_above_hook,
            torch.ones(num_envs, device=self.device) * 1.0,
            torch.zeros(num_envs, device=self.device)
        )

        # フックへの到達ボーナス（中央がフック近く）
        success_threshold = 0.1
        success_bonus = torch.where(
            next_cable_hook_dist < success_threshold,
            torch.ones(num_envs, device=self.device) * 15.0,
            torch.zeros(num_envs, device=self.device)
        )

        reward = transport_progress + proximity_reward + maintain_grasp + height_reward + success_bonus

        info = {
            "cable_hook_dist": cable_hook_dist,
            "transport_progress": transport_progress,
            "proximity_reward": proximity_reward,
            "maintain_grasp": maintain_grasp,
            "height_reward": height_reward,
            "success_bonus": success_bonus,
            "skill_success": next_cable_hook_dist < success_threshold,
        }

        return reward, info

    def _compute_hang_reward(
        self,
        obs: DualArmObservation,
        next_obs: DualArmObservation,
        action: torch.Tensor,
        gripper_state: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """Bimanual Hang スキルの報酬.

        目標: ケーブル中央(segments 4-5)をY字フックのV字部分に掛ける
        """
        num_envs = obs.left_ee_pos.shape[0]

        # ケーブル端点と中央を取得
        if obs.cable_center is not None:
            cable_center = obs.cable_center
            next_cable_center = next_obs.cable_center
            left_target = obs.cable_left_end
            right_target = obs.cable_right_end
        else:
            cable_center = obs.cable_pos
            next_cable_center = next_obs.cable_pos
            left_target = obs.cable_pos
            right_target = obs.cable_pos

        # ケーブル中央とフックの精密距離
        cable_hook_dist = torch.norm(cable_center - obs.hook_pos, dim=-1)
        next_cable_hook_dist = torch.norm(next_cable_center - next_obs.hook_pos, dim=-1)

        # 精密アプローチ報酬（指数的スケール）
        precision_reward = torch.exp(-cable_hook_dist * 20.0) * 5.0

        # 改善報酬
        improvement = (cable_hook_dist - next_cable_hook_dist) * 10.0

        # ケーブル中央の高さがフックより高いことを確認（掛ける前）
        cable_above_hook = cable_center[:, 2] > obs.hook_pos[:, 2]
        height_reward = torch.where(
            cable_above_hook,
            torch.ones(num_envs, device=self.device) * 2.0,
            torch.zeros(num_envs, device=self.device)
        )

        # 両端の把持維持
        left_dist = torch.norm(obs.left_ee_pos - left_target, dim=-1)
        right_dist = torch.norm(obs.right_ee_pos - right_target, dim=-1)
        maintain_grasp = torch.exp(-left_dist * 10.0) + torch.exp(-right_dist * 10.0)

        # Y字フックに掛けるための形状報酬
        # ケーブルがU字形状（両端が上、中央が下）であることを確認
        if obs.cable_left_end is not None:
            left_end_z = obs.cable_left_end[:, 2]
            right_end_z = obs.cable_right_end[:, 2]
            center_z = cable_center[:, 2]
            # U字形状: 両端が中央より高い
            u_shape = (left_end_z > center_z) & (right_end_z > center_z)
            u_shape_reward = torch.where(
                u_shape,
                torch.ones(num_envs, device=self.device) * 3.0,
                torch.zeros(num_envs, device=self.device)
            )

            # 両端がフックの両側に配置されているか（X-Y平面で広がっている）
            left_to_hook_xy = obs.cable_left_end[:, :2] - obs.hook_pos[:, :2]
            right_to_hook_xy = obs.cable_right_end[:, :2] - obs.hook_pos[:, :2]
            # 両端がフックを挟んでいるとき、内積が負になる
            spread_dot = (left_to_hook_xy * right_to_hook_xy).sum(dim=-1)
            spread_reward = torch.where(
                spread_dot < 0,  # フックを挟んでいる
                torch.ones(num_envs, device=self.device) * 2.0,
                torch.zeros(num_envs, device=self.device)
            )
        else:
            u_shape_reward = torch.zeros(num_envs, device=self.device)
            spread_reward = torch.zeros(num_envs, device=self.device)

        # フック掛け成功ボーナス
        # 成功条件: ケーブル中央がフック近傍 + U字形状
        hang_threshold = 0.05
        hang_success_condition = next_cable_hook_dist < hang_threshold
        hang_success = torch.where(
            hang_success_condition,
            torch.ones(num_envs, device=self.device) * 25.0,
            torch.zeros(num_envs, device=self.device)
        )

        reward = (
            precision_reward + improvement + height_reward +
            maintain_grasp + u_shape_reward + spread_reward + hang_success
        )

        info = {
            "cable_hook_dist": cable_hook_dist,
            "precision_reward": precision_reward,
            "improvement": improvement,
            "height_reward": height_reward,
            "maintain_grasp": maintain_grasp,
            "u_shape_reward": u_shape_reward,
            "spread_reward": spread_reward,
            "hang_success": hang_success,
            "skill_success": hang_success_condition,
        }

        return reward, info

    def _compute_release_reward(
        self,
        obs: DualArmObservation,
        next_obs: DualArmObservation,
        action: torch.Tensor,
        gripper_state: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """Bimanual Release スキルの報酬.

        目標: グリッパーを開いてケーブル両端を離す（中央はフックに掛かったまま）
        """
        num_envs = obs.left_ee_pos.shape[0]

        # ケーブル端点と中央を取得
        if obs.cable_center is not None:
            cable_center = obs.cable_center
            next_cable_center = next_obs.cable_center
            left_target = obs.cable_left_end
            right_target = obs.cable_right_end
            next_left_target = next_obs.cable_left_end
            next_right_target = next_obs.cable_right_end
        else:
            cable_center = obs.cable_pos
            next_cable_center = next_obs.cable_pos
            left_target = obs.cable_pos
            right_target = obs.cable_pos
            next_left_target = next_obs.cable_pos
            next_right_target = next_obs.cable_pos

        # グリッパーを開く報酬
        left_gripper_action = action[:, 7:9].mean(dim=-1)
        right_gripper_action = action[:, 16:18].mean(dim=-1)

        # 正の値=開く方向
        open_reward = (left_gripper_action + right_gripper_action) * self.gripper_weight

        # グリッパー同期
        gripper_sync = torch.exp(-torch.abs(left_gripper_action - right_gripper_action) * 2.0)

        # ケーブル中央がフック位置に留まっていることを確認
        cable_hook_dist = torch.norm(next_cable_center - next_obs.hook_pos, dim=-1)
        maintain_position = torch.exp(-cable_hook_dist * 10.0) * 2.0

        # EEをケーブル端点から離す
        left_dist = torch.norm(next_obs.left_ee_pos - next_left_target, dim=-1)
        right_dist = torch.norm(next_obs.right_ee_pos - next_right_target, dim=-1)

        # 離れていることに報酬
        retract_reward = torch.clamp(left_dist - 0.1, min=0) + torch.clamp(right_dist - 0.1, min=0)

        # 完了ボーナス
        # 成功条件: 両手がケーブルから離れ、中央がフックに掛かっている
        release_complete = (
            (left_dist > 0.15) &
            (right_dist > 0.15) &
            (cable_hook_dist < 0.08)
        )
        complete_bonus = torch.where(
            release_complete,
            torch.ones(num_envs, device=self.device) * 30.0,
            torch.zeros(num_envs, device=self.device)
        )

        reward = open_reward + gripper_sync + maintain_position + retract_reward + complete_bonus

        info = {
            "open_reward": open_reward,
            "gripper_sync": gripper_sync,
            "maintain_position": maintain_position,
            "retract_reward": retract_reward,
            "complete_bonus": complete_bonus,
            "cable_hook_dist": cable_hook_dist,
            "skill_success": release_complete,
        }

        return reward, info

    # =====================================================
    # ユーティリティ関数
    # =====================================================

    def _compute_velocity_penalty(self, obs: DualArmObservation) -> torch.Tensor:
        """関節速度ペナルティ."""
        left_vel_norm = torch.norm(obs.left_joint_vel, dim=-1)
        right_vel_norm = torch.norm(obs.right_joint_vel, dim=-1)
        return (left_vel_norm + right_vel_norm) * self.velocity_penalty_weight

    def _compute_action_penalty(self, action: torch.Tensor) -> torch.Tensor:
        """アクションペナルティ（過大なアクションを抑制）."""
        return torch.norm(action, dim=-1) * self.action_penalty_weight

    def check_skill_success(
        self,
        skill_name: str,
        obs: torch.Tensor,
        task_state: Optional[torch.Tensor] = None,
        threshold: Optional[float] = None,
    ) -> torch.Tensor:
        """スキル成功判定.

        Args:
            skill_name: スキル名
            obs: 観測テンソル (num_envs, 60) - 従来形式
            task_state: タスク状態 (num_envs, 44) - ケーブルセグメント付き（オプション）
            threshold: 成功判定閾値

        Returns:
            success: 成功フラグ (num_envs,)
        """
        # task_stateがある場合はそちらを使用
        if task_state is not None:
            parsed_obs = DualArmObservation.from_task_state(task_state)
        else:
            parsed_obs = DualArmObservation.from_flat_tensor(obs)

        # デフォルト閾値
        thresholds = {
            "bimanual_reach": 0.08,
            "bimanual_grasp": 0.03,
            "bimanual_lift": 0.9,  # 高さ
            "bimanual_transport": 0.1,
            "bimanual_hang": 0.05,
            "bimanual_release": 0.15,  # EE-Cable距離
        }

        if threshold is None:
            threshold = thresholds.get(skill_name, 0.1)

        if skill_name == "bimanual_reach":
            # 各手が対応するケーブル端点に到達
            if parsed_obs.cable_left_end is not None:
                left_dist = torch.norm(parsed_obs.left_ee_pos - parsed_obs.cable_left_end, dim=-1)
                right_dist = torch.norm(parsed_obs.right_ee_pos - parsed_obs.cable_right_end, dim=-1)
            else:
                left_dist = torch.norm(parsed_obs.left_ee_pos - parsed_obs.cable_pos, dim=-1)
                right_dist = torch.norm(parsed_obs.right_ee_pos - parsed_obs.cable_pos, dim=-1)
            return (left_dist < threshold) & (right_dist < threshold)

        elif skill_name == "bimanual_grasp":
            # 各手が対応するケーブル端点を把持
            if parsed_obs.cable_left_end is not None:
                left_dist = torch.norm(parsed_obs.left_ee_pos - parsed_obs.cable_left_end, dim=-1)
                right_dist = torch.norm(parsed_obs.right_ee_pos - parsed_obs.cable_right_end, dim=-1)
            else:
                left_dist = torch.norm(parsed_obs.left_ee_pos - parsed_obs.cable_pos, dim=-1)
                right_dist = torch.norm(parsed_obs.right_ee_pos - parsed_obs.cable_pos, dim=-1)
            return (left_dist < threshold) & (right_dist < threshold)

        elif skill_name == "bimanual_lift":
            # ケーブル中央が目標高さ以上
            if parsed_obs.cable_center is not None:
                return parsed_obs.cable_center[:, 2] > threshold
            else:
                return parsed_obs.cable_pos[:, 2] > threshold

        elif skill_name == "bimanual_transport":
            # ケーブル中央がフック近傍
            if parsed_obs.cable_center is not None:
                cable_hook_dist = torch.norm(parsed_obs.cable_center - parsed_obs.hook_pos, dim=-1)
            else:
                cable_hook_dist = torch.norm(parsed_obs.cable_pos - parsed_obs.hook_pos, dim=-1)
            return cable_hook_dist < threshold

        elif skill_name == "bimanual_hang":
            # ケーブル中央がフックに掛かっている
            if parsed_obs.cable_center is not None:
                cable_hook_dist = torch.norm(parsed_obs.cable_center - parsed_obs.hook_pos, dim=-1)
            else:
                cable_hook_dist = torch.norm(parsed_obs.cable_pos - parsed_obs.hook_pos, dim=-1)
            return cable_hook_dist < threshold

        elif skill_name == "bimanual_release":
            # 両手がケーブルから離れている
            if parsed_obs.cable_left_end is not None:
                left_dist = torch.norm(parsed_obs.left_ee_pos - parsed_obs.cable_left_end, dim=-1)
                right_dist = torch.norm(parsed_obs.right_ee_pos - parsed_obs.cable_right_end, dim=-1)
            else:
                left_dist = torch.norm(parsed_obs.left_ee_pos - parsed_obs.cable_pos, dim=-1)
                right_dist = torch.norm(parsed_obs.right_ee_pos - parsed_obs.cable_pos, dim=-1)
            return (left_dist > threshold) & (right_dist > threshold)

        else:
            return torch.zeros(obs.shape[0], dtype=torch.bool, device=self.device)

    def compute_skill_reward_from_task_state(
        self,
        skill_name: str,
        task_state: torch.Tensor,
        next_task_state: torch.Tensor,
        action: torch.Tensor,
        proprio: Optional[torch.Tensor] = None,
        next_proprio: Optional[torch.Tensor] = None,
        gripper_state: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """task_stateからスキル報酬を計算（DreamerV3連携用）.

        World Modelが予測したtask_stateを使って報酬を計算する。

        Args:
            skill_name: スキル名
            task_state: 現在のタスク状態 (num_envs, 44)
            next_task_state: 次のタスク状態 (num_envs, 44)
            action: 実行されたアクション (num_envs, 18)
            proprio: 現在のプロプリオ (num_envs, 34) - オプション
            next_proprio: 次のプロプリオ (num_envs, 34) - オプション
            gripper_state: グリッパー状態（オプション）

        Returns:
            reward: スキル報酬 (num_envs,)
            info: 報酬の内訳辞書
        """
        if skill_name not in self.skill_reward_functions:
            raise ValueError(f"Unknown skill: {skill_name}")

        # task_stateからDualArmObservationを構築
        current_obs = DualArmObservation.from_task_state(task_state, proprio)
        next_obs = DualArmObservation.from_task_state(next_task_state, next_proprio)

        # スキル固有報酬を計算
        reward, info = self.skill_reward_functions[skill_name](
            current_obs, next_obs, action, gripper_state
        )

        # 共通ペナルティを追加
        velocity_penalty = self._compute_velocity_penalty(current_obs)
        action_penalty = self._compute_action_penalty(action)

        reward = reward - velocity_penalty - action_penalty
        info["velocity_penalty"] = velocity_penalty
        info["action_penalty"] = action_penalty

        return reward, info
