# Copyright (c) 2024-2025, THREAD Project
# SPDX-License-Identifier: BSD-3-Clause
"""Dual Arm MSA Configuration - 双腕用モジュラースキルアーキテクチャ設定."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class DualArmMSAConfig:
    """双腕用Modular Skill Architecture設定.

    双腕操作（Franka Panda x2）のためのMSA設定。
    各スキルは両腕の協調動作として定義される。
    """

    # ====================
    # スキル定義
    # ====================
    skill_names: List[str] = field(default_factory=lambda: [
        "bimanual_reach",      # 両腕でケーブルに接近
        "bimanual_grasp",      # 両腕でケーブルを把持
        "bimanual_lift",       # ケーブルを持ち上げ
        "bimanual_transport",  # フックに向かって移動
        "bimanual_hang",       # フックにケーブルを掛ける
        "bimanual_release",    # グリッパーを開いて離す
    ])

    # スキル遷移制約（有効な遷移のみを定義）
    skill_transitions: Dict[str, List[str]] = field(default_factory=lambda: {
        "bimanual_reach": ["bimanual_grasp"],
        "bimanual_grasp": ["bimanual_lift", "bimanual_reach"],  # 失敗時はreachに戻る
        "bimanual_lift": ["bimanual_transport"],
        "bimanual_transport": ["bimanual_hang", "bimanual_lift"],  # 落とした場合はliftに戻る
        "bimanual_hang": ["bimanual_release", "bimanual_transport"],
        "bimanual_release": ["bimanual_reach"],  # タスク完了後、次のエピソードへ
    })

    # 初期スキル
    initial_skill: str = "bimanual_reach"

    # ====================
    # 次元設定（双腕用）
    # ====================
    # 観測空間: 60D
    # - Left arm: joint_pos(9) + joint_vel(9) + ee_pos(3) = 21
    # - Right arm: joint_pos(9) + joint_vel(9) + ee_pos(3) = 21
    # - Cable position: 3
    # - Hook position: 3
    # - Relative distances: 12 (left_ee-cable, right_ee-cable, cable-hook, etc.)
    state_dim: int = 60

    # 行動空間: 18D (9 joints x 2 arms)
    # - Left arm: 7 arm joints + 2 gripper = 9
    # - Right arm: 7 arm joints + 2 gripper = 9
    action_dim: int = 18

    # 潜在空間次元（World Modelからのエンコード後）
    latent_dim: int = 256

    # ====================
    # ネットワーク設定
    # ====================
    # スキルモジュールの隠れ層
    hidden_dims: List[int] = field(default_factory=lambda: [512, 256, 128])

    # アクティベーション関数
    activation: str = "gelu"

    # Layer Normalization使用
    use_layer_norm: bool = True

    # ====================
    # アダプター設定（LoRA風）
    # ====================
    adapter_rank: int = 32
    adapter_alpha: float = 1.0
    use_adapter: bool = True

    # ====================
    # スキルセレクター設定
    # ====================
    selector_hidden_dim: int = 256
    selector_num_layers: int = 3
    selector_temperature: float = 1.0  # Softmax温度

    # Q-Learning設定（スキル選択用）
    selector_gamma: float = 0.99
    selector_epsilon_start: float = 1.0
    selector_epsilon_end: float = 0.1
    selector_epsilon_decay: int = 10000

    # ====================
    # 学習設定
    # ====================
    learning_rate: float = 3e-4
    skill_learning_rate: float = 1e-4  # スキルモジュール用
    selector_learning_rate: float = 1e-4  # スキルセレクター用

    # PPO設定
    ppo_epochs: int = 5
    ppo_clip: float = 0.2
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    max_grad_norm: float = 0.5

    # バッチ設定
    batch_size: int = 512
    mini_batch_size: int = 64

    # ====================
    # 訓練設定
    # ====================
    # スキル別訓練イテレーション
    skill_pretrain_iterations: Dict[str, int] = field(default_factory=lambda: {
        "bimanual_reach": 2000,
        "bimanual_grasp": 3000,
        "bimanual_lift": 2000,
        "bimanual_transport": 2000,
        "bimanual_hang": 3000,
        "bimanual_release": 1000,
    })

    # 統合訓練イテレーション
    integrated_iterations: int = 10000

    # チェックポイント保存間隔
    save_interval: int = 500

    # ====================
    # デバイス設定
    # ====================
    device: str = "cuda"

    # ====================
    # 双腕特有設定
    # ====================
    # 腕間の協調報酬重み
    coordination_reward_weight: float = 0.1

    # グリッパー同期報酬重み
    gripper_sync_reward_weight: float = 0.05

    # 対称性ペナルティ重み（不必要な非対称動作を抑制）
    symmetry_penalty_weight: float = 0.01


@dataclass
class DualArmSkillConfig:
    """個別スキルの詳細設定."""

    name: str = ""

    # スキル固有の報酬重み
    primary_reward_weight: float = 1.0
    secondary_reward_weight: float = 0.5

    # スキル完了条件閾値
    success_threshold: float = 0.05  # メートル

    # スキルタイムアウト（ステップ数）
    max_steps: int = 200

    # スキル固有の行動スケール
    action_scale: float = 1.0


def get_default_skill_configs() -> Dict[str, DualArmSkillConfig]:
    """各スキルのデフォルト設定を取得."""
    return {
        "bimanual_reach": DualArmSkillConfig(
            name="bimanual_reach",
            primary_reward_weight=1.0,
            secondary_reward_weight=0.3,
            success_threshold=0.08,  # EE-Cable距離
            max_steps=150,
            action_scale=1.0,
        ),
        "bimanual_grasp": DualArmSkillConfig(
            name="bimanual_grasp",
            primary_reward_weight=1.0,
            secondary_reward_weight=0.5,
            success_threshold=0.03,  # グリッパー閉じ＋接触
            max_steps=100,
            action_scale=0.5,  # 細かい動作
        ),
        "bimanual_lift": DualArmSkillConfig(
            name="bimanual_lift",
            primary_reward_weight=1.0,
            secondary_reward_weight=0.4,
            success_threshold=0.1,  # 持ち上げ高さ
            max_steps=100,
            action_scale=0.8,
        ),
        "bimanual_transport": DualArmSkillConfig(
            name="bimanual_transport",
            primary_reward_weight=1.0,
            secondary_reward_weight=0.3,
            success_threshold=0.1,  # Cable-Hook距離
            max_steps=200,
            action_scale=1.0,
        ),
        "bimanual_hang": DualArmSkillConfig(
            name="bimanual_hang",
            primary_reward_weight=1.0,
            secondary_reward_weight=0.5,
            success_threshold=0.05,  # フック位置決め精度
            max_steps=150,
            action_scale=0.5,
        ),
        "bimanual_release": DualArmSkillConfig(
            name="bimanual_release",
            primary_reward_weight=1.0,
            secondary_reward_weight=0.2,
            success_threshold=0.5,  # グリッパー開き
            max_steps=50,
            action_scale=0.3,
        ),
    }


# デフォルト設定インスタンス
DEFAULT_DUAL_ARM_MSA_CONFIG = DualArmMSAConfig()
