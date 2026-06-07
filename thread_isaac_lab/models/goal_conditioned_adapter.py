#!/usr/bin/env python3
"""
Goal-Conditioned Skill Adapter with HER
ゴール条件付け学習 + Hindsight Experience Replay
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import random


@dataclass
class Transition:
    """経験の1ステップ"""
    state: torch.Tensor          # 現在状態latent (352D)
    action: torch.Tensor         # 行動 (18D)
    next_state: torch.Tensor     # 次状態latent (352D)
    reward: float                # 報酬
    done: bool                   # 終了フラグ
    goal: torch.Tensor           # ゴールlatent (352D)
    task_state: torch.Tensor     # タスク状態 (17D)
    next_task_state: torch.Tensor  # 次タスク状態 (17D)


@dataclass
class Episode:
    """1エピソード分の経験"""
    transitions: List[Transition]
    skill_name: str
    achieved_goal: bool


class HindsightExperienceReplay:
    """
    HER: Hindsight Experience Replay

    失敗したエピソードを、実際に到達した状態をゴールとして再利用
    """
    def __init__(
        self,
        capacity: int = 100000,
        her_ratio: float = 0.8,  # HERサンプルの割合
        strategy: str = "future"  # future, final, episode
    ):
        self.capacity = capacity
        self.her_ratio = her_ratio
        self.strategy = strategy
        self.buffer: deque = deque(maxlen=capacity)
        self.episodes: List[Episode] = []

    def add_episode(self, episode: Episode):
        """エピソードを追加"""
        self.episodes.append(episode)

        # 通常の経験を追加
        for t in episode.transitions:
            self.buffer.append(t)

        # HER: 失敗エピソードから追加経験を生成
        if not episode.achieved_goal and len(episode.transitions) > 0:
            her_transitions = self._generate_her_transitions(episode)
            for t in her_transitions:
                self.buffer.append(t)

    def _generate_her_transitions(self, episode: Episode) -> List[Transition]:
        """HERで追加経験を生成"""
        her_transitions = []
        transitions = episode.transitions

        for i, t in enumerate(transitions):
            if self.strategy == "future":
                # 将来の状態をゴールに
                future_indices = range(i + 1, len(transitions))
                if len(future_indices) > 0:
                    future_idx = random.choice(list(future_indices))
                    new_goal = transitions[future_idx].next_state
                    new_reward = self._compute_reward(
                        t.next_task_state,
                        transitions[future_idx].next_task_state,
                        episode.skill_name
                    )
                    her_transitions.append(Transition(
                        state=t.state,
                        action=t.action,
                        next_state=t.next_state,
                        reward=new_reward,
                        done=future_idx == len(transitions) - 1,
                        goal=new_goal,
                        task_state=t.task_state,
                        next_task_state=t.next_task_state
                    ))

            elif self.strategy == "final":
                # 最終状態をゴールに
                final_state = transitions[-1].next_state
                final_task_state = transitions[-1].next_task_state
                new_reward = self._compute_reward(
                    t.next_task_state,
                    final_task_state,
                    episode.skill_name
                )
                her_transitions.append(Transition(
                    state=t.state,
                    action=t.action,
                    next_state=t.next_state,
                    reward=new_reward,
                    done=i == len(transitions) - 1,
                    goal=final_state,
                    task_state=t.task_state,
                    next_task_state=t.next_task_state
                ))

            elif self.strategy == "episode":
                # ランダムな状態をゴールに
                random_idx = random.randint(0, len(transitions) - 1)
                new_goal = transitions[random_idx].next_state
                new_reward = self._compute_reward(
                    t.next_task_state,
                    transitions[random_idx].next_task_state,
                    episode.skill_name
                )
                her_transitions.append(Transition(
                    state=t.state,
                    action=t.action,
                    next_state=t.next_state,
                    reward=new_reward,
                    done=False,
                    goal=new_goal,
                    task_state=t.task_state,
                    next_task_state=t.next_task_state
                ))

        return her_transitions

    def _compute_reward(
        self,
        achieved_task_state: torch.Tensor,
        goal_task_state: torch.Tensor,
        skill_name: str
    ) -> float:
        """ゴール達成度に基づく報酬を計算"""
        # task_stateの距離で判定
        if isinstance(achieved_task_state, torch.Tensor):
            achieved = achieved_task_state.cpu().numpy()
            goal = goal_task_state.cpu().numpy()
        else:
            achieved = achieved_task_state
            goal = goal_task_state

        # 距離計算（task_stateの位置成分）
        distance = np.linalg.norm(achieved[:12] - goal[:12])  # pos components

        # スキル別の成功閾値
        thresholds = {
            "bimanual_reach": 0.05,
            "bimanual_grasp": 0.03,
            "bimanual_lift": 0.05,
            "bimanual_transport": 0.10,
            "bimanual_hang": 0.05,
            "bimanual_release": 0.05
        }
        threshold = thresholds.get(skill_name, 0.05)

        if distance < threshold:
            return 0.0  # 成功
        else:
            return -1.0  # 失敗

    def sample(self, batch_size: int) -> List[Transition]:
        """バッチサンプリング"""
        return random.sample(list(self.buffer), min(batch_size, len(self.buffer)))

    def __len__(self):
        return len(self.buffer)


class GoalConditionedSkillAdapter(nn.Module):
    """
    Goal-Conditioned Skill Adapter

    入力: current_latent (352D) + goal_latent (352D) + predictions (1760D) = 2464D
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

        # 入力次元: current + goal + predictions
        self.input_dim = latent_dim * (2 + prediction_horizon)  # 352 * 7 = 2464

        # Dynamics予測器（凍結予定）
        self.dynamics = nn.Sequential(
            nn.Linear(latent_dim + action_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, latent_dim)
        )

        # 予測用の仮行動生成器
        self.action_predictor = nn.Sequential(
            nn.Linear(latent_dim * 2, 128),  # current + goal
            nn.ReLU(),
            nn.Linear(128, action_dim),
            nn.Tanh()
        )

        # スキル埋め込み
        self.skill_embedding = nn.Embedding(num_skills, 64)

        # ゴール差分エンコーダ（current - goal の関係を学習）
        self.goal_diff_encoder = nn.Sequential(
            nn.Linear(latent_dim * 2, 256),
            nn.ReLU(),
            nn.Linear(256, 128)
        )

        # ベースポリシー
        self.base_policy = nn.Sequential(
            nn.Linear(self.input_dim + 128 + 64, 512),  # +128 goal_diff, +64 skill
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim)
        )

        # スキル別LoRAアダプタ
        self.skill_loras = nn.ModuleList([
            nn.Sequential(
                nn.Linear(self.input_dim + 128 + 64, lora_rank, bias=False),
                nn.Linear(lora_rank, action_dim, bias=False)
            )
            for _ in range(num_skills)
        ])

        # LoRAスケール初期化
        for lora in self.skill_loras:
            nn.init.zeros_(lora[1].weight)

        self.skill_names = [
            "bimanual_reach", "bimanual_grasp", "bimanual_lift",
            "bimanual_transport", "bimanual_hang", "bimanual_release"
        ]

    def freeze_dynamics(self):
        """Dynamics予測器を凍結"""
        for param in self.dynamics.parameters():
            param.requires_grad = False

    def predict_future(
        self,
        current_latent: torch.Tensor,
        goal_latent: torch.Tensor
    ) -> torch.Tensor:
        """短期予測（ゴール条件付き）"""
        batch_size = current_latent.shape[0]
        predicted_states = []

        state = current_latent
        for t in range(self.prediction_horizon):
            # ゴール方向への行動を予測
            action = self.action_predictor(torch.cat([state, goal_latent], dim=-1))

            # 次状態を予測
            next_state = self.dynamics(torch.cat([state, action], dim=-1))
            predicted_states.append(next_state)
            state = next_state

        return torch.cat(predicted_states, dim=-1)  # (batch, horizon * latent_dim)

    def forward(
        self,
        current_latent: torch.Tensor,
        goal_latent: torch.Tensor,
        skill_idx: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            current_latent: 現在状態 (batch, 352)
            goal_latent: ゴール状態 (batch, 352)
            skill_idx: スキルインデックス (batch,) or int

        Returns:
            action: (batch, 18)
        """
        batch_size = current_latent.shape[0]

        # 短期予測（ゴール条件付き）
        predicted_states = self.predict_future(current_latent, goal_latent)

        # ゴール差分エンコード
        goal_diff = self.goal_diff_encoder(
            torch.cat([current_latent, goal_latent], dim=-1)
        )

        # 全て結合
        combined = torch.cat([
            current_latent,      # 352D
            goal_latent,         # 352D
            predicted_states     # 1760D
        ], dim=-1)  # 2464D

        # スキル埋め込み
        if isinstance(skill_idx, int):
            skill_idx = torch.full(
                (batch_size,), skill_idx,
                dtype=torch.long, device=current_latent.device
            )
        skill_emb = self.skill_embedding(skill_idx)  # 64D

        # ベース入力
        x = torch.cat([combined, goal_diff, skill_emb], dim=-1)  # 2464 + 128 + 64

        # ベースポリシー
        base_action = self.base_policy(x)

        # スキル別LoRA適応
        lora_adjustment = torch.zeros_like(base_action)
        for i in range(self.num_skills):
            mask = (skill_idx == i).float().unsqueeze(-1)
            lora_out = self.skill_loras[i](x) * 0.1  # scale
            lora_adjustment = lora_adjustment + mask * lora_out

        action = torch.tanh(base_action + lora_adjustment)
        return action

    def get_skill_idx(self, skill_name: str) -> int:
        return self.skill_names.index(skill_name)


class GoalConditionedActorCritic(nn.Module):
    """Actor-Critic版（PPO訓練用）"""
    def __init__(
        self,
        latent_dim: int = 352,
        action_dim: int = 18,
        prediction_horizon: int = 5,
        num_skills: int = 6
    ):
        super().__init__()
        self.latent_dim = latent_dim
        self.input_dim = latent_dim * (2 + prediction_horizon) + 128 + 64

        # Actor
        self.actor = GoalConditionedSkillAdapter(
            latent_dim=latent_dim,
            action_dim=action_dim,
            prediction_horizon=prediction_horizon,
            num_skills=num_skills
        )

        # Critic
        self.critic = nn.Sequential(
            nn.Linear(self.input_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )

        # 行動の標準偏差
        self.log_std = nn.Parameter(torch.zeros(action_dim))

    def forward(
        self,
        current_latent: torch.Tensor,
        goal_latent: torch.Tensor,
        skill_idx: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns:
            action_mean, action_std, value
        """
        action_mean = self.actor(current_latent, goal_latent, skill_idx)
        action_std = self.log_std.exp().expand_as(action_mean)

        # Critic用の入力
        batch_size = current_latent.shape[0]
        predicted = self.actor.predict_future(current_latent, goal_latent)
        goal_diff = self.actor.goal_diff_encoder(
            torch.cat([current_latent, goal_latent], dim=-1)
        )

        if isinstance(skill_idx, int):
            skill_idx = torch.full(
                (batch_size,), skill_idx,
                dtype=torch.long, device=current_latent.device
            )
        skill_emb = self.actor.skill_embedding(skill_idx)

        x = torch.cat([
            current_latent, goal_latent, predicted, goal_diff, skill_emb
        ], dim=-1)
        value = self.critic(x)

        return action_mean, action_std, value

    def freeze_dynamics(self):
        self.actor.freeze_dynamics()


class GoalImageBank:
    """スキル別ゴール画像バンク"""
    def __init__(self, latent_dim: int = 352):
        self.latent_dim = latent_dim
        self.goals: Dict[str, List[torch.Tensor]] = {
            "bimanual_reach": [],
            "bimanual_grasp": [],
            "bimanual_lift": [],
            "bimanual_transport": [],
            "bimanual_hang": [],
            "bimanual_release": []
        }

    def add_goal(self, skill_name: str, goal_latent: torch.Tensor):
        """ゴールlatentを追加"""
        self.goals[skill_name].append(goal_latent.cpu())

    def sample_goal(self, skill_name: str, device: str = "cuda") -> Optional[torch.Tensor]:
        """ランダムにゴールをサンプル"""
        if len(self.goals[skill_name]) == 0:
            return None
        goal = random.choice(self.goals[skill_name])
        return goal.to(device)

    def save(self, path: str):
        """保存"""
        torch.save(self.goals, path)

    def load(self, path: str):
        """ロード"""
        self.goals = torch.load(path)

    def __repr__(self):
        counts = {k: len(v) for k, v in self.goals.items()}
        return f"GoalImageBank({counts})"


# テスト
if __name__ == "__main__":
    print("Testing Goal-Conditioned Skill Adapter + HER...")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    batch_size = 4
    latent_dim = 352

    # モデルテスト
    model = GoalConditionedActorCritic().to(device)

    current = torch.randn(batch_size, latent_dim, device=device)
    goal = torch.randn(batch_size, latent_dim, device=device)
    skill_idx = torch.tensor([0, 1, 2, 3], device=device)

    action_mean, action_std, value = model(current, goal, skill_idx)

    print(f"Current latent: {current.shape}")
    print(f"Goal latent: {goal.shape}")
    print(f"Action mean: {action_mean.shape}")
    print(f"Value: {value.shape}")

    # パラメータ数
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total params: {total:,}")
    print(f"Trainable params: {trainable:,}")

    # HERテスト
    print("\nTesting HER...")
    her = HindsightExperienceReplay(capacity=10000, strategy="future")

    # ダミーエピソード
    transitions = [
        Transition(
            state=torch.randn(latent_dim),
            action=torch.randn(18),
            next_state=torch.randn(latent_dim),
            reward=-1.0,
            done=False,
            goal=torch.randn(latent_dim),
            task_state=torch.randn(17),
            next_task_state=torch.randn(17)
        )
        for _ in range(10)
    ]
    episode = Episode(transitions=transitions, skill_name="bimanual_reach", achieved_goal=False)

    her.add_episode(episode)
    print(f"Buffer size after 1 episode: {len(her)}")

    samples = her.sample(5)
    print(f"Sampled {len(samples)} transitions")

    # ゴールバンクテスト
    print("\nTesting GoalImageBank...")
    bank = GoalImageBank()
    for _ in range(5):
        bank.add_goal("bimanual_reach", torch.randn(latent_dim))
    print(bank)

    sampled_goal = bank.sample_goal("bimanual_reach", device)
    print(f"Sampled goal shape: {sampled_goal.shape}")

    print("\n✓ All tests passed!")
