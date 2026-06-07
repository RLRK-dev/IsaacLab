"""Isaac Sim bridge for Franka dual-arm MCP server."""


class SimConnector:
    def __init__(self, sim_gpu: int = 2):
        self.sim_gpu = sim_gpu
        self.connected = False

    async def connect(self):
        """Stub: connect to Isaac Sim."""
        print(f"SimConnector: connecting to Isaac Sim on GPU {self.sim_gpu}...")
        self.connected = True

    async def get_state(self, arm: str) -> dict:
        """Return mock robot state."""
        # Mock data for development. Replace with Isaac Sim API calls.
        mock_state = {
            "joint_positions": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
            "ee_position": [0.307, 0.0, 0.487],
            "ee_orientation": [1.0, 0.0, 0.0, 0.0],
            "gripper_width": 0.04,
        }
        if arm == "both":
            return {"left": mock_state, "right": mock_state}
        return {arm: mock_state}

    async def move_ee(self, arm: str, delta: list[float], speed: str) -> dict:
        """Mock: return success with slightly adjusted position."""
        return {
            "success": True,
            "final_ee_position": [0.307 + delta[0], 0.0 + delta[1], 0.487 + delta[2]],
            "error": None,
        }

    async def move_to(
        self, arm: str, position: list[float], orientation: list[float], speed: str
    ) -> dict:
        """Mock: move to absolute position."""
        return {"success": True, "final_ee_position": position, "error": None}

    async def move_joints(
        self, arm: str, positions: list[float], speed: str
    ) -> dict:
        """Mock: move to joint positions."""
        return {"success": True, "final_joint_positions": positions, "error": None}

    async def home(self, arm: str) -> dict:
        """Mock: return to home position."""
        return {"success": True}

    async def grasp(self, arm: str, width: float, force: float) -> dict:
        """Mock: close gripper."""
        return {
            "success": True,
            "final_width": width,
            "object_detected": width < 0.01,
        }

    async def release(self, arm: str, width: float) -> dict:
        """Mock: open gripper."""
        return {"success": True, "final_width": width}

    async def capture_image(self, camera: str) -> str:
        """Mock: return a placeholder image path."""
        return f"/tmp/franka_mcp/{camera}_capture.png"

    async def reset_scene(self, scenario: str) -> dict:
        """Mock: reset simulation scene."""
        return {"success": True, "scenario": scenario or "default"}

    async def step_sim(self, steps: int) -> dict:
        """Mock: step simulation forward."""
        return {"success": True, "sim_time": steps * 0.01}
