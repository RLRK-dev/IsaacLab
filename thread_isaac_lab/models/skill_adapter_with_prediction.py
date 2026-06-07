"""
Skill Adapter with Short-term Prediction
短期予測（5ステップ）を活用するSkill Adapter
"""
import torch
import torch.nn as nn
from typing import Dict, Tuple, Optional

class DynamicsPredictor(nn.Module):
    """World Model Dynamicsの推論部分（凍結）"""
    def __init__(self, latent_dim: int = 352, action_dim: int = 18):
        super().__init__()
        self.latent_dim = latent_dim
        self.action_dim = action_dim

        # Dynamics MLP
        self.dynamics = nn.Sequential(
            nn.Linear(latent_dim + action_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, latent_dim)  # 次状態のlatent
        )

    def forward(self, latent: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """1ステップ予測"""
        x = torch.cat([latent, action], dim=-1)
        next_latent = self.dynamics(x)
        return next_latent


class ShortTermPredictor(nn.Module):
    """短期予測（複数ステップ）"""
    def __init__(
        self,
        latent_dim: int = 352,
        action_dim: int = 18,
        horizon: int = 5
    ):
        super().__init__()
        self.latent_dim = latent_dim
        self.action_dim = action_dim
        self.horizon = horizon

        self.dynamics = DynamicsPredictor(latent_dim, action_dim)

        # 予測用の仮行動生成器（現在の行動を繰り返すか、学習）
        self.action_predictor = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
            nn.Tanh()
        )

    def forward(
        self,
        latent: torch.Tensor,
        current_action: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        短期予測を実行

        Args:
            latent: 現在の状態latent (batch, 352)
            current_action: 現在の行動 (batch, 18)、Noneなら予測

        Returns:
            predicted_states: (batch, horizon * latent_dim)
        """
        batch_size = latent.shape[0]
        predicted_states = []

        state = latent
        for t in range(self.horizon):
            # 行動を決定
            if current_action is not None and t == 0:
                action = current_action
            else:
                action = self.action_predictor(state)

            # 次状態を予測
            next_state = self.dynamics(state, action)
            predicted_states.append(next_state)
            state = next_state

        # (batch, horizon * latent_dim)
        return torch.cat(predicted_states, dim=-1)


class LoRALayer(nn.Module):
    """Low-Rank Adaptation層"""
    def __init__(self, in_dim: int, out_dim: int, rank: int = 16):
        super().__init__()
        self.lora_down = nn.Linear(in_dim, rank, bias=False)
        self.lora_up = nn.Linear(rank, out_dim, bias=False)
        self.scale = 0.1

        nn.init.kaiming_uniform_(self.lora_down.weight)
        nn.init.zeros_(self.lora_up.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.lora_up(self.lora_down(x)) * self.scale


class SkillAdapterWithPrediction(nn.Module):
    """
    短期予測を活用するSkill Adapter

    入力: latent (352D) + predicted_states (352D × 5) = 2112D
    出力: action (18D)
    """
    def __init__(
        self,
        latent_dim: int = 352,
        action_dim: int = 18,
        prediction_horizon: int = 5,
        num_skills: int = 6,
        lora_rank: int = 16
    ):
        super().__init__()
        self.latent_dim = latent_dim
        self.action_dim = action_dim
        self.prediction_horizon = prediction_horizon
        self.num_skills = num_skills

        # 入力次元: 現在latent + 予測latent
        self.input_dim = latent_dim * (1 + prediction_horizon)  # 352 * 6 = 2112

        # 短期予測器（凍結予定）
        self.predictor = ShortTermPredictor(
            latent_dim=latent_dim,
            action_dim=action_dim,
            horizon=prediction_horizon
        )

        # スキル埋め込み
        self.skill_embedding = nn.Embedding(num_skills, 64)

        # ベースポリシー（共有）
        self.base_policy = nn.Sequential(
            nn.Linear(self.input_dim + 64, 512),  # +64 for skill embedding
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim)
        )

        # スキル別LoRAアダプタ
        self.skill_loras = nn.ModuleList([
            LoRALayer(self.input_dim + 64, action_dim, rank=lora_rank)
            for _ in range(num_skills)
        ])

        # スキル名マッピング
        self.skill_names = [
            "bimanual_reach",
            "bimanual_grasp",
            "bimanual_lift",
            "bimanual_transport",
            "bimanual_hang",
            "bimanual_release"
        ]

    def freeze_predictor(self):
        """予測器を凍結"""
        for param in self.predictor.dynamics.parameters():
            param.requires_grad = False

    def forward(
        self,
        latent: torch.Tensor,
        skill_idx: torch.Tensor,
        current_action: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            latent: 現在の状態latent (batch, 352)
            skill_idx: スキルインデックス (batch,) または int
            current_action: 現在の行動 (batch, 18)

        Returns:
            action: 適応された行動 (batch, 18)
        """
        batch_size = latent.shape[0]

        # 短期予測
        predicted_states = self.predictor(latent, current_action)

        # 現在latent + 予測を結合
        combined = torch.cat([latent, predicted_states], dim=-1)  # (batch, 2112)

        # スキル埋め込み
        if isinstance(skill_idx, int):
            skill_idx = torch.full((batch_size,), skill_idx, dtype=torch.long, device=latent.device)
        skill_emb = self.skill_embedding(skill_idx)  # (batch, 64)

        # ベース入力
        x = torch.cat([combined, skill_emb], dim=-1)  # (batch, 2176)

        # ベースポリシー
        base_action = self.base_policy(x)

        # スキル別LoRA適応
        lora_adjustment = torch.zeros_like(base_action)
        for i in range(self.num_skills):
            mask = (skill_idx == i).float().unsqueeze(-1)
            lora_out = self.skill_loras[i](x)
            lora_adjustment = lora_adjustment + mask * lora_out

        action = base_action + lora_adjustment
        return torch.tanh(action)  # [-1, 1]に正規化

    def get_skill_idx(self, skill_name: str) -> int:
        """スキル名からインデックスを取得"""
        return self.skill_names.index(skill_name)


class SkillAdapterActorCritic(nn.Module):
    """Actor-Critic版（PPO訓練用）"""
    def __init__(
        self,
        latent_dim: int = 352,
        action_dim: int = 18,
        prediction_horizon: int = 5,
        num_skills: int = 6
    ):
        super().__init__()
        self.input_dim = latent_dim * (1 + prediction_horizon)

        # Actor（SkillAdapterWithPrediction）
        self.actor = SkillAdapterWithPrediction(
            latent_dim=latent_dim,
            action_dim=action_dim,
            prediction_horizon=prediction_horizon,
            num_skills=num_skills
        )

        # Critic（状態価値関数）
        self.critic = nn.Sequential(
            nn.Linear(self.input_dim + 64, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )

        # 行動の標準偏差（学習可能）
        self.log_std = nn.Parameter(torch.zeros(action_dim))

    def forward(
        self,
        latent: torch.Tensor,
        skill_idx: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns:
            action_mean: 行動平均
            action_std: 行動標準偏差
            value: 状態価値
        """
        action_mean = self.actor(latent, skill_idx)
        action_std = self.log_std.exp().expand_as(action_mean)

        # Critic用の入力を構築
        predicted_states = self.actor.predictor(latent, None)
        combined = torch.cat([latent, predicted_states], dim=-1)

        batch_size = latent.shape[0]
        if isinstance(skill_idx, int):
            skill_idx = torch.full((batch_size,), skill_idx, dtype=torch.long, device=latent.device)
        skill_emb = self.actor.skill_embedding(skill_idx)

        x = torch.cat([combined, skill_emb], dim=-1)
        value = self.critic(x)

        return action_mean, action_std, value


# テスト
if __name__ == "__main__":
    print("Testing SkillAdapterWithPrediction...")

    batch_size = 4
    latent_dim = 352
    action_dim = 18

    model = SkillAdapterWithPrediction(
        latent_dim=latent_dim,
        action_dim=action_dim,
        prediction_horizon=5
    )

    # ダミー入力
    latent = torch.randn(batch_size, latent_dim)
    skill_idx = torch.tensor([0, 1, 2, 3])  # 各サンプルに異なるスキル

    # Forward
    action = model(latent, skill_idx)

    print(f"Input latent: {latent.shape}")
    print(f"Skill indices: {skill_idx}")
    print(f"Output action: {action.shape}")
    print(f"Action range: [{action.min():.3f}, {action.max():.3f}]")

    # パラメータ数
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total params: {total_params:,}")
    print(f"Trainable params: {trainable_params:,}")

    # Actor-Critic版
    print("\nTesting SkillAdapterActorCritic...")
    ac_model = SkillAdapterActorCritic()
    action_mean, action_std, value = ac_model(latent, skill_idx)
    print(f"Action mean: {action_mean.shape}")
    print(f"Action std: {action_std.shape}")
    print(f"Value: {value.shape}")

    print("\n✓ All tests passed!")
