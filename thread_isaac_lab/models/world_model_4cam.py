"""World Model with 4 Cameras for THREAD Project.

4-Camera Version for demo_data_v1 format.

Architecture:
    [Input]
    ├── front_left_img (256x256)
    ├── front_right_img (256x256)
    ├── back_img (256x256)
    ├── overhead_img (256x256)
    ├── proprio (34D)
    └── task_state (44D)

         ↓

    [Encoders]
    ├── Visual Encoders → 256D (64 × 4 cameras)
    ├── Proprio Encoder → 64D
    └── Task State Encoder → 32D

         ↓

    [Fusion] → 352D latent (256 + 64 + 32)

         ↓

    [Dynamics + Predictors]
    ├── next_proprio (34D)
    ├── next_task_state (44D)
    └── reward (1D)
"""

from dataclasses import dataclass
import torch
import torch.nn as nn


@dataclass
class WorldModel4CamConfig:
    """Configuration for World Model with 4 Cameras."""

    # Image dimensions (all cameras use 256x256)
    img_size: int = 256

    # Feature dimensions
    per_camera_feature_dim: int = 64   # Feature dim per camera
    num_cameras: int = 4               # front_left, front_right, back, overhead
    proprio_dim: int = 34              # Proprioception (left 17 + right 17)
    task_state_dim: int = 44           # Task state (cable segments + positions + distances)
    action_dim: int = 18               # Action (left 9 + right 9)

    # Encoder output dimensions
    visual_latent_dim: int = 256       # 64 × 4 cameras = 256D
    proprio_latent_dim: int = 64
    task_latent_dim: int = 32

    # Fusion: 256 + 64 + 32 = 352D
    fusion_dim: int = 352

    # Dynamics hidden size
    dynamics_hidden: int = 512

    # Training
    learning_rate: float = 1e-4
    batch_size: int = 32


class CameraEncoder(nn.Module):
    """Encoder for 256x256 camera images -> 64D feature."""

    def __init__(self, feature_dim: int = 64):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 4, stride=2, padding=1),   # 256 -> 128
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 4, stride=2, padding=1),  # 128 -> 64
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 4, stride=2, padding=1), # 64 -> 32
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 256, 4, stride=2, padding=1), # 32 -> 16
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, 4, stride=2, padding=1), # 16 -> 8
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(256, feature_dim),
        )

    def forward(self, x):
        return self.encoder(x)


class CameraDecoder(nn.Module):
    """Decoder for 64D feature -> 256x256 image."""

    def __init__(self, feature_dim: int = 64):
        super().__init__()
        self.fc = nn.Linear(feature_dim, 256 * 8 * 8)
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, 4, stride=2, padding=1),  # 8 -> 16
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(128, 64, 4, stride=2, padding=1),   # 16 -> 32
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, 4, stride=2, padding=1),    # 32 -> 64
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32, 16, 4, stride=2, padding=1),    # 64 -> 128
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(16, 3, 4, stride=2, padding=1),     # 128 -> 256
            nn.Sigmoid(),
        )

    def forward(self, z):
        x = self.fc(z).view(-1, 256, 8, 8)
        return self.decoder(x)


class ProprioEncoder(nn.Module):
    """Encoder for proprioception (34D -> 64D)."""

    def __init__(self, proprio_dim: int = 34, hidden_dim: int = 128, output_dim: int = 64):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(proprio_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.encoder(x)


class TaskStateEncoder(nn.Module):
    """Encoder for task state (44D -> 32D)."""

    def __init__(self, task_dim: int = 44, hidden_dim: int = 64, output_dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(task_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.encoder(x)


class FourCameraAutoencoder(nn.Module):
    """Autoencoder for 4 cameras (Phase 1 training)."""

    def __init__(self, config: WorldModel4CamConfig):
        super().__init__()
        self.config = config

        # Encoders (one per camera)
        self.front_left_encoder = CameraEncoder(config.per_camera_feature_dim)
        self.front_right_encoder = CameraEncoder(config.per_camera_feature_dim)
        self.back_encoder = CameraEncoder(config.per_camera_feature_dim)
        self.overhead_encoder = CameraEncoder(config.per_camera_feature_dim)

        # Decoders (one per camera)
        self.front_left_decoder = CameraDecoder(config.per_camera_feature_dim)
        self.front_right_decoder = CameraDecoder(config.per_camera_feature_dim)
        self.back_decoder = CameraDecoder(config.per_camera_feature_dim)
        self.overhead_decoder = CameraDecoder(config.per_camera_feature_dim)

    def forward(self, front_left, front_right, back, overhead):
        # Encode
        z_front_left = self.front_left_encoder(front_left)
        z_front_right = self.front_right_encoder(front_right)
        z_back = self.back_encoder(back)
        z_overhead = self.overhead_encoder(overhead)

        # Decode
        recon_front_left = self.front_left_decoder(z_front_left)
        recon_front_right = self.front_right_decoder(z_front_right)
        recon_back = self.back_decoder(z_back)
        recon_overhead = self.overhead_decoder(z_overhead)

        return {
            "front_left_recon": recon_front_left,
            "front_right_recon": recon_front_right,
            "back_recon": recon_back,
            "overhead_recon": recon_overhead,
            "z_front_left": z_front_left,
            "z_front_right": z_front_right,
            "z_back": z_back,
            "z_overhead": z_overhead,
        }


class WorldModel4Cam(nn.Module):
    """World Model with 4 cameras for dynamics prediction."""

    def __init__(self, config: WorldModel4CamConfig):
        super().__init__()
        self.config = config

        # Visual encoders (one per camera)
        self.front_left_encoder = CameraEncoder(config.per_camera_feature_dim)
        self.front_right_encoder = CameraEncoder(config.per_camera_feature_dim)
        self.back_encoder = CameraEncoder(config.per_camera_feature_dim)
        self.overhead_encoder = CameraEncoder(config.per_camera_feature_dim)

        # State encoders
        self.proprio_encoder = ProprioEncoder(
            proprio_dim=config.proprio_dim,
            output_dim=config.proprio_latent_dim
        )
        self.task_encoder = TaskStateEncoder(
            task_dim=config.task_state_dim,
            output_dim=config.task_latent_dim
        )

        # Dynamics model: latent + action -> next latent
        dynamics_input_dim = config.fusion_dim + config.action_dim  # 352 + 18 = 370
        self.dynamics = nn.Sequential(
            nn.Linear(dynamics_input_dim, config.dynamics_hidden),
            nn.ReLU(inplace=True),
            nn.Linear(config.dynamics_hidden, config.dynamics_hidden),
            nn.ReLU(inplace=True),
            nn.Linear(config.dynamics_hidden, config.fusion_dim),
        )

        # Predictors
        self.proprio_predictor = nn.Sequential(
            nn.Linear(config.fusion_dim, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, config.proprio_dim),
        )

        self.task_predictor = nn.Sequential(
            nn.Linear(config.fusion_dim, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, config.task_state_dim),
        )

        self.reward_predictor = nn.Sequential(
            nn.Linear(config.fusion_dim, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
        )

    def encode_visual(self, front_left, front_right, back, overhead):
        """Encode 4 camera images to visual latent."""
        z_fl = self.front_left_encoder(front_left)
        z_fr = self.front_right_encoder(front_right)
        z_b = self.back_encoder(back)
        z_o = self.overhead_encoder(overhead)
        return torch.cat([z_fl, z_fr, z_b, z_o], dim=-1)  # 256D

    def encode(self, front_left, front_right, back, overhead, proprio, task_state):
        """Encode full observation to latent state."""
        z_visual = self.encode_visual(front_left, front_right, back, overhead)
        z_proprio = self.proprio_encoder(proprio)
        z_task = self.task_encoder(task_state)
        return torch.cat([z_visual, z_proprio, z_task], dim=-1)  # 352D

    def forward(self, front_left, front_right, back, overhead, proprio, task_state, action):
        """Forward pass for dynamics prediction.

        Args:
            front_left, front_right, back, overhead: Camera images [B, 3, 256, 256]
            proprio: Proprioception [B, 34]
            task_state: Task state [B, 44]
            action: Action [B, 18]

        Returns:
            dict with predicted next_proprio, next_task_state, reward
        """
        # Encode current state
        z_t = self.encode(front_left, front_right, back, overhead, proprio, task_state)

        # Predict next latent
        z_action = torch.cat([z_t, action], dim=-1)
        z_next = self.dynamics(z_action)

        # Decode predictions
        pred_proprio = self.proprio_predictor(z_next)
        pred_task = self.task_predictor(z_next)
        pred_reward = self.reward_predictor(z_next)

        return {
            "z_t": z_t,
            "z_next": z_next,
            "pred_proprio": pred_proprio,
            "pred_task_state": pred_task,
            "pred_reward": pred_reward,
        }

    def load_pretrained_encoders(self, autoencoder_path: str, device: torch.device):
        """Load pretrained visual encoders from Phase 1 autoencoder."""
        checkpoint = torch.load(autoencoder_path, map_location=device, weights_only=False)
        state_dict = checkpoint.get("model_state_dict", checkpoint)

        # Map autoencoder keys to world model keys
        encoder_names = [
            "front_left_encoder",
            "front_right_encoder",
            "back_encoder",
            "overhead_encoder",
        ]

        # Build new state dict for encoders only
        new_state_dict = {}
        for enc_name in encoder_names:
            prefix = f"{enc_name}."
            for key, value in state_dict.items():
                if key.startswith(prefix):
                    new_state_dict[key] = value

        # Load with strict=False to only update matching keys
        missing, unexpected = self.load_state_dict(new_state_dict, strict=False)
        loaded = len(new_state_dict)

        print(f"[WorldModel4Cam] Loaded {loaded} pretrained encoder parameters")
