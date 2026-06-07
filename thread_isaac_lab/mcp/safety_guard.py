"""Safety guard for validating motion and gripper commands before execution."""

import math

DEFAULT_CONFIG = {
    "max_delta_m": 0.15,
    "max_joint_vel": 1.0,
    "workspace_bounds": {
        "x_min": -0.5,
        "x_max": 0.5,
        "y_min": -0.5,
        "y_max": 0.5,
        "z_min": 0.0,
        "z_max": 0.8,
    },
    "joint_limits": {
        "lower": [-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973],
        "upper": [2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973],
    },
    "min_dual_arm_distance": 0.10,
    "table_height": 0.0,
}


class SafetyGuard:
    def __init__(self, config: dict | None = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}

    def check_move_ee(
        self, arm: str, current_ee: list[float], delta: list[float]
    ) -> dict:
        """Validate a delta EE move before execution."""
        max_d = self.config["max_delta_m"]
        bounds = self.config["workspace_bounds"]
        table_h = self.config["table_height"]
        warnings: list[str] = []

        # Check 1: Delta magnitude
        for i, (axis, val) in enumerate(zip(["dx", "dy", "dz"], delta)):
            if abs(val) > max_d:
                return {
                    "allowed": False,
                    "clamped_delta": None,
                    "warnings": [],
                    "error": f"{axis}={val:.4f} exceeds max_delta_m={max_d}",
                }

        # Check 2: Target position within workspace
        target = [current_ee[j] + delta[j] for j in range(3)]
        axes = ["x", "y", "z"]
        mins = [bounds["x_min"], bounds["y_min"], bounds["z_min"]]
        maxs = [bounds["x_max"], bounds["y_max"], bounds["z_max"]]
        for j in range(3):
            if target[j] < mins[j] or target[j] > maxs[j]:
                return {
                    "allowed": False,
                    "clamped_delta": None,
                    "warnings": [],
                    "error": (
                        f"Target {axes[j]}={target[j]:.4f} out of workspace "
                        f"[{mins[j]}, {maxs[j]}]"
                    ),
                }

        # Check 3: Table collision
        if target[2] < table_h:
            return {
                "allowed": False,
                "clamped_delta": None,
                "warnings": [],
                "error": f"Target z={target[2]:.4f} below table_height={table_h}",
            }

        return {
            "allowed": True,
            "clamped_delta": delta,
            "warnings": warnings,
            "error": None,
        }

    def check_move_to(self, arm: str, target_position: list[float]) -> dict:
        """Validate an absolute EE move before execution."""
        bounds = self.config["workspace_bounds"]
        table_h = self.config["table_height"]

        # Check 1: Workspace bounds
        axes = ["x", "y", "z"]
        mins = [bounds["x_min"], bounds["y_min"], bounds["z_min"]]
        maxs = [bounds["x_max"], bounds["y_max"], bounds["z_max"]]
        for j in range(3):
            if target_position[j] < mins[j] or target_position[j] > maxs[j]:
                return {
                    "allowed": False,
                    "clamped_delta": None,
                    "warnings": [],
                    "error": (
                        f"Target {axes[j]}={target_position[j]:.4f} out of workspace "
                        f"[{mins[j]}, {maxs[j]}]"
                    ),
                }

        # Check 2: Table collision
        if target_position[2] < table_h:
            return {
                "allowed": False,
                "clamped_delta": None,
                "warnings": [],
                "error": (
                    f"Target z={target_position[2]:.4f} below "
                    f"table_height={table_h}"
                ),
            }

        return {"allowed": True, "clamped_delta": None, "warnings": [], "error": None}

    def check_move_joints(self, arm: str, target_positions: list[float]) -> dict:
        """Validate joint positions before execution."""
        # Check 1: Joint count
        if len(target_positions) != 7:
            return {
                "allowed": False,
                "clamped_delta": None,
                "warnings": [],
                "error": (
                    f"Expected 7 joint positions, got {len(target_positions)}"
                ),
            }

        # Check 2: Joint limits
        lower = self.config["joint_limits"]["lower"]
        upper = self.config["joint_limits"]["upper"]
        for i in range(7):
            if target_positions[i] < lower[i] or target_positions[i] > upper[i]:
                return {
                    "allowed": False,
                    "clamped_delta": None,
                    "warnings": [],
                    "error": (
                        f"Joint {i}: {target_positions[i]:.4f} outside limits "
                        f"[{lower[i]:.4f}, {upper[i]:.4f}]"
                    ),
                }

        return {"allowed": True, "clamped_delta": None, "warnings": [], "error": None}

    def check_state(self, state: dict) -> dict:
        """Post-execution sanity check on robot state."""
        joints = state.get("joint_positions", [])
        ee = state.get("ee_position", [])

        # Check 1: NaN / Inf
        for val in joints + ee:
            if math.isnan(val) or math.isinf(val):
                return {
                    "ok": False,
                    "emergency_stop": True,
                    "reason": "NaN or Inf detected in state",
                }

        # Check 2: Joint limits (with 0.1 rad margin)
        lower = self.config["joint_limits"]["lower"]
        upper = self.config["joint_limits"]["upper"]
        margin = 0.1
        for i, val in enumerate(joints):
            if val < lower[i] - margin or val > upper[i] + margin:
                return {
                    "ok": False,
                    "emergency_stop": False,
                    "reason": (
                        f"Joint {i}: {val:.4f} outside limits "
                        f"[{lower[i]:.4f}, {upper[i]:.4f}] (margin={margin})"
                    ),
                }

        # Check 3: Workspace violation (with 0.05m margin)
        bounds = self.config["workspace_bounds"]
        ws_margin = 0.05
        axes = ["x", "y", "z"]
        mins = [bounds["x_min"], bounds["y_min"], bounds["z_min"]]
        maxs = [bounds["x_max"], bounds["y_max"], bounds["z_max"]]
        for j in range(min(len(ee), 3)):
            if ee[j] < mins[j] - ws_margin or ee[j] > maxs[j] + ws_margin:
                return {
                    "ok": False,
                    "emergency_stop": False,
                    "reason": (
                        f"EE {axes[j]}={ee[j]:.4f} outside workspace "
                        f"[{mins[j]}, {maxs[j]}] (margin={ws_margin})"
                    ),
                }

        return {"ok": True, "emergency_stop": False, "reason": None}

    def check_dual_arm_distance(
        self, left_ee: list[float], right_ee: list[float]
    ) -> dict:
        """Check distance between left and right EE positions."""
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(left_ee, right_ee)))
        min_dist = self.config["min_dual_arm_distance"]
        if dist < min_dist:
            return {
                "allowed": False,
                "distance": dist,
                "error": (
                    f"Dual arm distance {dist:.4f}m < minimum {min_dist}m"
                ),
            }
        return {"allowed": True, "distance": dist, "error": None}
