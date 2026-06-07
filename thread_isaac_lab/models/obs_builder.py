"""obs_builder.py — 24D observation space builder for SOMA/THREAD.

Reference: thread-vault/04-Specs/SOMA.md (24D obs構成)

Dims:
  0-6:   left_joint_pos (7)        — robot_left.data.joint_pos[:, 0:7]
  7-13:  right_joint_pos (7)       — robot_right.data.joint_pos[:, 0:7]
  14-16: cable_midpoint_pos (3)    — API or vision pipeline (A9)
  17:    cable_tension (1)         — approx from cable joint wrench
  18:    ee_pos_error_left (1)     — ||EE_left - nearest_cable_seg||
  19:    ee_pos_error_right (1)    — ||EE_right - nearest_cable_seg||
  20:    force_derivative_left (1) — d/dt grip_effort_left
  21:    force_derivative_right (1)— d/dt grip_effort_right
  22:    grip_effort_left (1)      — mean(applied_torque[:, 7:9])
  23:    grip_effort_right (1)     — mean(applied_torque[:, 7:9])
"""

from __future__ import annotations

import json
import os
from typing import Optional

import numpy as np
import torch
from thread_isaac_lab.configs.task_config import OBS_DIM, OBS_MODES, OBS_NORMALIZATION, FALLBACK


class ObsBuilder24D:
    """Builds 24D observation tensor for SOMA/THREAD dual-arm cable manipulation.

    Maintains internal state for force_derivative computation (requires prev step).
    Call reset() when starting a new episode/env.
    """

    def __init__(self, num_envs: int, device: str, obs_mode: str = "24d",
                 vision_pipeline=None):
        """Initialize 24D obs builder.

        Args:
            num_envs: Number of parallel environments.
            device: Torch device string.
            obs_mode: '18d', '22d', or '24d'.
            vision_pipeline: Optional VisionPipelineStage1to3 instance.
                If provided, cable_midpoint_pos (dims 14-16) will be
                estimated from cameras instead of sim API.
                Only supported for num_envs=1.
        """
        self.num_envs = num_envs
        self.device = device
        self.obs_dim = OBS_DIM  # always build full 24D internally
        # Obs mode: controls output dimensionality
        if obs_mode not in OBS_MODES:
            raise ValueError(f"Unknown obs_mode '{obs_mode}'. Valid: {list(OBS_MODES.keys())}")
        self.obs_mode = obs_mode
        self.output_dim = OBS_MODES[obs_mode]["dim"]
        self._output_end = OBS_MODES[obs_mode]["end"]
        self._prev_grip_effort_left = torch.zeros(num_envs, device=device)
        self._prev_grip_effort_right = torch.zeros(num_envs, device=device)
        self._step_count = 0
        # Vision pipeline (A9): camera-based cable_midpoint estimation
        self._vision_pipeline = vision_pipeline
        self._vision_meta_last: Optional[dict] = None
        # Precompute normalization tensors (full 24D for internal use)
        self._norm_scale_full = torch.tensor(
            OBS_NORMALIZATION["scale"], dtype=torch.float32, device=device)
        self._norm_offset_full = torch.tensor(
            OBS_NORMALIZATION["offset"], dtype=torch.float32, device=device)
        # Sliced normalization tensors for output dim
        self._norm_scale = self._norm_scale_full[:self._output_end]
        self._norm_offset = self._norm_offset_full[:self._output_end]
        # Load p99 bounds for anomaly detection (B4)
        self._p99_upper, self._p99_lower = self._load_p99_bounds(device)

    def reset(self, env_ids=None):
        """Reset internal state (call at episode start)."""
        if env_ids is None:
            self._prev_grip_effort_left.zero_()
            self._prev_grip_effort_right.zero_()
            self._step_count = 0
        else:
            self._prev_grip_effort_left[env_ids] = 0.0
            self._prev_grip_effort_right[env_ids] = 0.0

    def build(
        self,
        robot_left,
        robot_right,
        cable,
        hand_body_left: int,
        hand_body_right: int,
        env_origins=None,
        dt: float = 1.0 / 120.0,
        sim_steps_elapsed: int = 1,
    ) -> torch.Tensor:
        """Build 24D obs tensor.

        Args:
            robot_left: Left arm Articulation
            robot_right: Right arm Articulation
            cable: Cable Articulation
            hand_body_left: Body index for left EE
            hand_body_right: Body index for right EE
            env_origins: (N, 3) env origin offsets or None
            dt: Physics timestep for force_derivative
            sim_steps_elapsed: Number of sim steps since last build() call

        Returns:
            obs: (num_envs, 24) tensor
        """
        N = self.num_envs
        obs = torch.zeros(N, self.obs_dim, device=self.device)

        # --- 0-6: left_joint_pos ---
        obs[:, 0:7] = robot_left.data.joint_pos[:, 0:7]

        # --- 7-13: right_joint_pos ---
        obs[:, 7:14] = robot_right.data.joint_pos[:, 0:7]

        # --- 14-16: cable_midpoint_pos ---
        cable_pos = cable.data.body_pos_w[:, :, :3]  # (N, num_seg, 3)
        # Always compute API midpoint (needed for ee_error + comparison)
        cable_mid = cable_pos.mean(dim=1)  # (N, 3)
        if env_origins is not None:
            cable_mid = cable_mid - env_origins
        self._cable_mid_api = cable_mid

        if self._vision_pipeline is not None and N == 1:
            # A9: Camera-based estimation (only for single-env)
            midpoint_np, meta = self._vision_pipeline.estimate_cable_midpoint(dt=dt)
            self._vision_meta_last = meta
            cable_mid_vision = torch.tensor(
                midpoint_np, dtype=torch.float32, device=self.device
            ).unsqueeze(0)  # (1, 3)
            if env_origins is not None:
                cable_mid_vision = cable_mid_vision - env_origins
            obs[:, 14:17] = cable_mid_vision
        else:
            # Default: API-based
            obs[:, 14:17] = cable_mid
            self._vision_meta_last = None

        # --- 17: cable_tension ---
        # Approximate from body_incoming_joint_wrench at center segment.
        # Force norm on the middle segment's incoming joint.
        num_seg = cable.data.body_pos_w.shape[1]
        mid_seg = num_seg // 2
        try:
            wrench = cable.data.body_incoming_joint_wrench_b  # (N, num_bodies, 6)
            force_vec = wrench[:, mid_seg, :3]  # (N, 3)
            tension = torch.norm(force_vec, dim=-1)  # (N,)
            obs[:, 17] = tension
        except (AttributeError, RuntimeError):
            # Fallback: estimate tension from segment stretch
            if num_seg >= 2:
                seg_dists = torch.norm(
                    cable_pos[:, 1:, :] - cable_pos[:, :-1, :], dim=-1
                )  # (N, num_seg-1)
                obs[:, 17] = seg_dists.mean(dim=-1)

        # --- 18: ee_pos_error_left ---
        ee_left = robot_left.data.body_pos_w[:, hand_body_left, :3]  # (N, 3)
        if env_origins is not None:
            ee_left_local = ee_left - env_origins
        else:
            ee_left_local = ee_left
        # Distance to nearest cable segment
        diff_l = cable_mid.unsqueeze(1) - cable_pos  # broadcast trick: use per-seg
        # Actually compute per-segment distance
        if env_origins is not None:
            cable_local = cable_pos - env_origins.unsqueeze(1)
        else:
            cable_local = cable_pos
        dist_l = torch.norm(
            ee_left_local.unsqueeze(1) - cable_local, dim=-1
        )  # (N, num_seg)
        obs[:, 18] = dist_l.min(dim=1).values  # (N,)

        # --- 19: ee_pos_error_right ---
        ee_right = robot_right.data.body_pos_w[:, hand_body_right, :3]  # (N, 3)
        if env_origins is not None:
            ee_right_local = ee_right - env_origins
        else:
            ee_right_local = ee_right
        dist_r = torch.norm(
            ee_right_local.unsqueeze(1) - cable_local, dim=-1
        )  # (N, num_seg)
        obs[:, 19] = dist_r.min(dim=1).values  # (N,)

        # --- 22: grip_effort_left ---
        # Mean of |applied_torque| on finger joints (j7, j8).
        # Absolute value because j7/j8 have opposite signs (fingers move in opposite dirs).
        grip_eff_l = robot_left.data.applied_torque[:, 7:9].abs().mean(dim=-1)  # (N,)
        obs[:, 22] = grip_eff_l

        # --- 23: grip_effort_right ---
        grip_eff_r = robot_right.data.applied_torque[:, 7:9].abs().mean(dim=-1)  # (N,)
        obs[:, 23] = grip_eff_r

        # --- 20: force_derivative_left ---
        # Use actual elapsed time = sim_steps_elapsed * dt
        actual_dt = max(sim_steps_elapsed, 1) * dt
        if self._step_count > 0:
            obs[:, 20] = (grip_eff_l - self._prev_grip_effort_left) / actual_dt
        # else: 0.0 (first step)

        # --- 21: force_derivative_right ---
        if self._step_count > 0:
            obs[:, 21] = (grip_eff_r - self._prev_grip_effort_right) / actual_dt

        # Update state for next call
        self._prev_grip_effort_left = grip_eff_l.clone()
        self._prev_grip_effort_right = grip_eff_r.clone()
        self._step_count += 1

        return self.slice_obs(obs)

    def slice_obs(self, obs: torch.Tensor) -> torch.Tensor:
        """Slice full 24D obs to output_dim based on obs_mode.

        Args:
            obs: (num_envs, 24) full obs tensor
        Returns:
            (num_envs, output_dim) sliced obs tensor
        """
        if self._output_end == self.obs_dim:
            return obs
        return obs[:, :self._output_end].contiguous()

    def normalize(self, obs: torch.Tensor) -> torch.Tensor:
        """Normalize obs to approx [0, 1] using p5/p95 fixed scale.

        Args:
            obs: (num_envs, output_dim) obs tensor (already sliced by build())
        Returns:
            (num_envs, output_dim) normalized obs tensor
        """
        return obs * self._norm_scale + self._norm_offset

    @staticmethod
    def _load_p99_bounds(device: str):
        """Load p99/min bounds from obs24d_summary.json for anomaly detection."""
        json_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            OBS_NORMALIZATION["source"])
        # Try absolute path relative to IsaacLab root
        if not os.path.exists(json_path):
            json_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "data",
                "heuristic_logs", "obs24d_summary.json")
        try:
            with open(json_path) as f:
                stats = json.load(f)
            p99 = torch.tensor(stats["overall"]["p99"], dtype=torch.float32, device=device)
            mins = torch.tensor(stats["overall"]["min"], dtype=torch.float32, device=device)
            # Add 10% margin with minimum absolute margin of 0.01
            span = p99 - mins
            margin = torch.clamp(span * 0.1, min=0.01)
            upper = p99 + margin
            lower = mins - margin
            return upper, lower
        except (FileNotFoundError, KeyError):
            # Fallback: no bounds (disable range check)
            return None, None

    def is_anomalous(self, obs: torch.Tensor) -> torch.Tensor:
        """Check each env for obs anomalies (B4 fallback conditions).

        Args:
            obs: (N, 24) raw obs tensor

        Returns:
            (N,) bool tensor — True if env has anomalous obs
        """
        N = obs.shape[0]
        anomalous = torch.zeros(N, dtype=torch.bool, device=self.device)

        # 1. NaN/Inf check
        if FALLBACK.get("obs_nan_inf", True):
            has_nan_inf = torch.isnan(obs).any(dim=1) | torch.isinf(obs).any(dim=1)
            anomalous |= has_nan_inf

        # 2. Out-of-range check (p99 bounds, sliced to output dim)
        if FALLBACK.get("obs_out_of_range_p99", True) and self._p99_upper is not None:
            upper = self._p99_upper[:self._output_end]
            lower = self._p99_lower[:self._output_end]
            out_upper = (obs > upper).any(dim=1)
            out_lower = (obs < lower).any(dim=1)
            anomalous |= out_upper | out_lower

        # 3. Grip effort spike check (only if grip_effort dims are in output)
        spike_ratio = FALLBACK.get("grip_effort_spike_ratio", 0.5)
        if spike_ratio > 0 and self._step_count > 0 and self._output_end >= 24:
            # grip_effort is at dims 22 (left) and 23 (right)
            grip_l = obs[:, 22]
            grip_r = obs[:, 23]
            # PD close p95 = 200N
            spike_threshold = 200.0 * spike_ratio  # 100N
            delta_l = (grip_l - self._prev_grip_effort_left).abs()
            delta_r = (grip_r - self._prev_grip_effort_right).abs()
            anomalous |= (delta_l > spike_threshold) | (delta_r > spike_threshold)

        return anomalous

    @property
    def vision_meta(self) -> Optional[dict]:
        """Metadata from the last vision pipeline call (None if API-based)."""
        return self._vision_meta_last

    @property
    def cable_mid_api(self) -> Optional[torch.Tensor]:
        """API-based cable midpoint from the last build() call (for comparison)."""
        return getattr(self, "_cable_mid_api", None)

    def format_obs(self, obs: torch.Tensor, env_idx: int = 0) -> str:
        """Format obs for logging."""
        o = obs[env_idx]
        d = self._output_end
        parts = [f"[OBS{d}D]"]
        parts.append(f"j_L=[{o[0]:.3f}..{o[6]:.3f}]")
        parts.append(f"j_R=[{o[7]:.3f}..{o[13]:.3f}]")
        parts.append(f"cable=({o[14]:.3f},{o[15]:.3f},{o[16]:.3f})")
        parts.append(f"tension={o[17]:.2f}")
        if d >= 20:
            parts.append(f"ee_err=({o[18]:.4f},{o[19]:.4f})")
        if d >= 22:
            parts.append(f"f_dot=({o[20]:.1f},{o[21]:.1f})")
        if d >= 24:
            parts.append(f"grip=({o[22]:.2f},{o[23]:.2f})")
        return " ".join(parts)
