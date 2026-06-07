#!/usr/bin/env python3
"""Goal-Conditioned Reward System for DreamerV3.

各スキルのゴール画像を設定し、World Modelの潜在空間で
現在状態とゴール状態の類似度から報酬を計算する。

物理的な距離は使用せず、以下を組み合わせる:
1. World Modelの予測報酬 (pred_reward)
2. 潜在空間でのゴールとの類似度
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class SkillGoal:
    """スキルごとのゴール定義."""
    skill_name: str
    goal_images: Dict[str, torch.Tensor]  # カメラ名 → ゴール画像
    goal_latent: Optional[torch.Tensor] = None  # エンコード済み潜在表現
    description: str = ""


class GoalConditionedRewardCalculator:
    """ゴール条件付き報酬計算器.

    World Modelの潜在空間でゴールとの類似度を計算し、
    pred_rewardと組み合わせて最終報酬を出力する。
    """

    def __init__(
        self,
        world_model,
        device: str = "cuda",
        similarity_weight: float = 1.0,
        pred_reward_weight: float = 1.0,
        success_threshold: float = 0.9,
    ):
        """
        Args:
            world_model: 訓練済みWorld Model (visual_encoder必須)
            device: 使用デバイス
            similarity_weight: 潜在空間類似度の重み
            pred_reward_weight: World Model予測報酬の重み
            success_threshold: 成功判定のコサイン類似度閾値
        """
        self.world_model = world_model
        self.device = device
        self.similarity_weight = similarity_weight
        self.pred_reward_weight = pred_reward_weight
        self.success_threshold = success_threshold

        # スキルごとのゴール
        self.skill_goals: Dict[str, SkillGoal] = {}

        # スキル順序（タスク進行順）
        self.skill_sequence = [
            "bimanual_reach",
            "bimanual_grasp",
            "bimanual_lift",
            "bimanual_transport",
            "bimanual_hang",
            "bimanual_release",
        ]

    def register_goal(
        self,
        skill_name: str,
        goal_images: Dict[str, torch.Tensor],
        description: str = "",
    ):
        """スキルのゴール画像を登録.

        Args:
            skill_name: スキル名
            goal_images: カメラ名 → 画像テンソル (C, H, W) or (1, C, H, W)
            description: ゴールの説明
        """
        # 画像を正規化して保存
        normalized_images = {}
        for cam_name, img in goal_images.items():
            if img.dim() == 3:
                img = img.unsqueeze(0)  # (C, H, W) → (1, C, H, W)
            normalized_images[cam_name] = img.to(self.device)

        # ゴール画像をエンコード
        with torch.no_grad():
            goal_latent = self.world_model.visual_encoder(normalized_images)

        self.skill_goals[skill_name] = SkillGoal(
            skill_name=skill_name,
            goal_images=normalized_images,
            goal_latent=goal_latent,
            description=description,
        )

        print(f"[Goal] Registered goal for '{skill_name}': {description}")

    def register_goal_from_path(
        self,
        skill_name: str,
        image_paths: Dict[str, str],
        description: str = "",
    ):
        """ファイルパスからゴール画像を登録.

        Args:
            skill_name: スキル名
            image_paths: カメラ名 → 画像ファイルパス
            description: ゴールの説明
        """
        import torchvision.transforms as T
        from PIL import Image

        transform = T.Compose([
            T.Resize((256, 256)),
            T.ToTensor(),
        ])

        goal_images = {}
        for cam_name, path in image_paths.items():
            img = Image.open(path).convert('RGB')
            goal_images[cam_name] = transform(img)

        self.register_goal(skill_name, goal_images, description)

    def compute_reward(
        self,
        skill_name: str,
        current_images: Dict[str, torch.Tensor],
        pred_reward: torch.Tensor,
        current_latent: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """スキル報酬を計算.

        Args:
            skill_name: 現在のスキル名
            current_images: 現在のカメラ画像 {cam_name: (batch, C, H, W)}
            pred_reward: World Modelの予測報酬 (batch,) or (batch, 1)
            current_latent: 事前計算済み潜在表現（オプション）

        Returns:
            reward: 最終報酬 (batch,)
            info: 報酬内訳
        """
        if skill_name not in self.skill_goals:
            # ゴールが登録されていない場合はpred_rewardのみ
            return pred_reward.squeeze(-1), {"pred_reward": pred_reward.squeeze(-1)}

        goal = self.skill_goals[skill_name]
        batch_size = pred_reward.shape[0]

        # 現在状態をエンコード
        if current_latent is None:
            with torch.no_grad():
                current_latent = self.world_model.visual_encoder(current_images)

        # ゴール潜在表現をバッチサイズに拡張
        goal_latent = goal.goal_latent.expand(batch_size, -1)

        # コサイン類似度を計算
        similarity = F.cosine_similarity(current_latent, goal_latent, dim=-1)

        # 類似度を0-1に正規化（-1～1 → 0～1）
        normalized_similarity = (similarity + 1) / 2

        # 成功判定
        success = similarity > self.success_threshold

        # 成功ボーナス
        success_bonus = torch.where(
            success,
            torch.ones(batch_size, device=self.device) * 10.0,
            torch.zeros(batch_size, device=self.device)
        )

        # 最終報酬
        pred_reward_squeezed = pred_reward.squeeze(-1)
        reward = (
            normalized_similarity * self.similarity_weight +
            pred_reward_squeezed * self.pred_reward_weight +
            success_bonus
        )

        info = {
            "similarity": similarity,
            "normalized_similarity": normalized_similarity,
            "pred_reward": pred_reward_squeezed,
            "success_bonus": success_bonus,
            "skill_success": success,
        }

        return reward, info

    def compute_reward_from_latent(
        self,
        skill_name: str,
        current_latent: torch.Tensor,
        pred_reward: torch.Tensor,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """潜在表現から直接報酬を計算（高速版）.

        Args:
            skill_name: 現在のスキル名
            current_latent: 現在の潜在表現 (batch, latent_dim)
            pred_reward: World Modelの予測報酬 (batch,) or (batch, 1)

        Returns:
            reward: 最終報酬 (batch,)
            info: 報酬内訳
        """
        return self.compute_reward(
            skill_name=skill_name,
            current_images={},
            pred_reward=pred_reward,
            current_latent=current_latent,
        )

    def check_skill_success(
        self,
        skill_name: str,
        current_latent: torch.Tensor,
    ) -> torch.Tensor:
        """スキル成功判定.

        Args:
            skill_name: スキル名
            current_latent: 現在の潜在表現 (batch, latent_dim)

        Returns:
            success: 成功フラグ (batch,)
        """
        if skill_name not in self.skill_goals:
            return torch.zeros(current_latent.shape[0], dtype=torch.bool, device=self.device)

        goal = self.skill_goals[skill_name]
        batch_size = current_latent.shape[0]
        goal_latent = goal.goal_latent.expand(batch_size, -1)

        similarity = F.cosine_similarity(current_latent, goal_latent, dim=-1)
        return similarity > self.success_threshold

    def get_next_skill(self, current_skill: str) -> Optional[str]:
        """次のスキルを取得.

        Args:
            current_skill: 現在のスキル名

        Returns:
            next_skill: 次のスキル名（最後の場合はNone）
        """
        if current_skill not in self.skill_sequence:
            return None

        idx = self.skill_sequence.index(current_skill)
        if idx + 1 < len(self.skill_sequence):
            return self.skill_sequence[idx + 1]
        return None

    def save_goals(self, save_dir: str):
        """ゴール画像と設定を保存.

        Args:
            save_dir: 保存ディレクトリ
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        config = {
            "similarity_weight": self.similarity_weight,
            "pred_reward_weight": self.pred_reward_weight,
            "success_threshold": self.success_threshold,
            "skills": {},
        }

        for skill_name, goal in self.skill_goals.items():
            skill_dir = save_path / skill_name
            skill_dir.mkdir(exist_ok=True)

            # ゴール画像を保存
            image_paths = {}
            for cam_name, img in goal.goal_images.items():
                img_path = skill_dir / f"{cam_name}.pt"
                torch.save(img.cpu(), img_path)
                image_paths[cam_name] = str(img_path)

            config["skills"][skill_name] = {
                "description": goal.description,
                "image_paths": image_paths,
            }

        # 設定を保存
        with open(save_path / "goal_config.json", "w") as f:
            json.dump(config, f, indent=2)

        print(f"[Goal] Saved {len(self.skill_goals)} goals to {save_dir}")

    def load_goals(self, load_dir: str):
        """ゴール画像と設定を読み込み.

        Args:
            load_dir: 読み込みディレクトリ
        """
        load_path = Path(load_dir)
        config_path = load_path / "goal_config.json"

        if not config_path.exists():
            print(f"[Goal] No config found at {config_path}")
            return

        with open(config_path) as f:
            config = json.load(f)

        self.similarity_weight = config.get("similarity_weight", 1.0)
        self.pred_reward_weight = config.get("pred_reward_weight", 1.0)
        self.success_threshold = config.get("success_threshold", 0.9)

        for skill_name, skill_config in config["skills"].items():
            goal_images = {}
            for cam_name, img_path in skill_config["image_paths"].items():
                goal_images[cam_name] = torch.load(img_path)

            self.register_goal(
                skill_name=skill_name,
                goal_images=goal_images,
                description=skill_config.get("description", ""),
            )

        print(f"[Goal] Loaded {len(self.skill_goals)} goals from {load_dir}")


def create_goal_images_from_simulation(
    env,
    world_model,
    camera_names: List[str],
    save_dir: str,
    skills: Optional[List[str]] = None,
):
    """シミュレーションからゴール画像を収集.

    各スキルの成功状態でスクリーンショットを撮影し、
    ゴール画像として保存する。

    Args:
        env: Isaac Lab環境
        world_model: World Model（エンコード用）
        camera_names: カメラ名リスト
        save_dir: 保存ディレクトリ
        skills: 収集するスキルリスト（Noneの場合は全スキル）
    """
    if skills is None:
        skills = [
            "bimanual_reach",
            "bimanual_grasp",
            "bimanual_lift",
            "bimanual_transport",
            "bimanual_hang",
            "bimanual_release",
        ]

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    print(f"[Goal Collection] Collecting goal images for {len(skills)} skills")
    print(f"[Goal Collection] Cameras: {camera_names}")
    print(f"[Goal Collection] Save to: {save_dir}")

    # TODO: 実装 - 各スキルの成功状態を手動またはスクリプトで達成し、
    # その時点のカメラ画像を保存する

    print("[Goal Collection] NOTE: Manual goal image collection required")
    print("  1. Run simulation to achieve each skill's goal state")
    print("  2. Save screenshots using the register_goal method")


# 使用例
if __name__ == "__main__":
    print("Goal-Conditioned Reward System")
    print("=" * 60)
    print("""
使用方法:

1. World Modelを読み込み
   model = FourCameraWorldModel(config)
   model.load_state_dict(checkpoint)

2. GoalConditionedRewardCalculatorを作成
   reward_calc = GoalConditionedRewardCalculator(model)

3. 各スキルのゴール画像を登録
   reward_calc.register_goal(
       skill_name="bimanual_grasp",
       goal_images={"front_left": img1, "front_right": img2, "back": img3},
       description="両手でケーブル両端を把持した状態"
   )

4. DreamerV3訓練時に報酬を計算
   reward, info = reward_calc.compute_reward(
       skill_name="bimanual_grasp",
       current_images=current_images,
       pred_reward=world_model_output['pred_reward'],
   )
""")
