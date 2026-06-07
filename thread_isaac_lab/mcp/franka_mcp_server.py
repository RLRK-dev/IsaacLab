"""Franka Dual-Arm MCP Server for Claude CLI."""

from .safety_guard import SafetyGuard
from .sim_connector import SimConnector
from .state_manager import StateManager
from .vlm_connector import VLMConnector

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("franka-dual-arm")

sim_connector = SimConnector()
state_manager = StateManager()
vlm_connector = VLMConnector()
safety = SafetyGuard()


# --- Perception ---


@mcp.tool()
async def get_state(arm: str = "both") -> dict:
    """Get current robot state (joint positions, EE pose, gripper width).

    Args:
        arm: Which arm to query. One of "left", "right", "both".
    """
    state = await sim_connector.get_state(arm)
    state_manager.record(state)
    return state


@mcp.tool()
async def look(camera: str = "front", query: str = "") -> dict:
    """Capture an image and optionally describe it with VLM.

    Args:
        camera: Camera to use. One of "front", "wrist_left", "wrist_right", "overhead".
        query: Optional question to ask the VLM about the image.
    """
    image_path = await sim_connector.capture_image(camera)
    description = await vlm_connector.describe(image_path, query)
    return {"description": description, "image_path": image_path}


# --- Motion ---


@mcp.tool()
async def move_ee(
    arm: str,
    dx: float = 0.0,
    dy: float = 0.0,
    dz: float = 0.0,
    drx: float = 0.0,
    dry: float = 0.0,
    drz: float = 0.0,
    speed: str = "normal",
) -> dict:
    """Move end-effector by a relative delta.

    Args:
        arm: Which arm to move. "left" or "right".
        dx: Delta x in meters.
        dy: Delta y in meters.
        dz: Delta z in meters.
        drx: Delta rotation x in radians.
        dry: Delta rotation y in radians.
        drz: Delta rotation z in radians.
        speed: Movement speed. One of "slow", "normal", "fast".
    """
    # Get current state for safety check
    both = await sim_connector.get_state("both")
    current_ee = both[arm]["ee_position"]
    delta = [dx, dy, dz]

    # Pre-check: delta and workspace
    check = safety.check_move_ee(arm, current_ee, delta)
    if not check["allowed"]:
        return {"success": False, "final_ee_position": None, "error": check["error"]}

    # Pre-check: dual arm distance
    other = "right" if arm == "left" else "left"
    other_ee = both[other]["ee_position"]
    moved_ee = [current_ee[i] + delta[i] for i in range(3)]
    if arm == "left":
        dist_check = safety.check_dual_arm_distance(moved_ee, other_ee)
    else:
        dist_check = safety.check_dual_arm_distance(other_ee, moved_ee)
    if not dist_check["allowed"]:
        return {
            "success": False,
            "final_ee_position": None,
            "error": dist_check["error"],
        }

    # Execute
    result = await sim_connector.move_ee(arm, delta, speed)

    # Post-check state
    new_state = await sim_connector.get_state(arm)
    state_manager.record(new_state)
    post = safety.check_state(new_state[arm])
    if post["emergency_stop"]:
        return {
            "success": False,
            "final_ee_position": None,
            "error": f"EMERGENCY STOP: {post['reason']}",
        }

    return result


@mcp.tool()
async def move_to(
    arm: str,
    x: float,
    y: float,
    z: float,
    qx: float = 0.0,
    qy: float = 0.0,
    qz: float = 0.0,
    qw: float = 1.0,
    speed: str = "normal",
) -> dict:
    """Move end-effector to an absolute position.

    Args:
        arm: Which arm to move. "left" or "right".
        x: Target x position in meters.
        y: Target y position in meters.
        z: Target z position in meters.
        qx: Target orientation quaternion x.
        qy: Target orientation quaternion y.
        qz: Target orientation quaternion z.
        qw: Target orientation quaternion w.
        speed: Movement speed. One of "slow", "normal", "fast".
    """
    position = [x, y, z]
    orientation = [qx, qy, qz, qw]

    # Pre-check: workspace bounds
    check = safety.check_move_to(arm, position)
    if not check["allowed"]:
        return {"success": False, "final_ee_position": None, "error": check["error"]}

    # Pre-check: dual arm distance
    both = await sim_connector.get_state("both")
    other = "right" if arm == "left" else "left"
    other_ee = both[other]["ee_position"]
    if arm == "left":
        dist_check = safety.check_dual_arm_distance(position, other_ee)
    else:
        dist_check = safety.check_dual_arm_distance(other_ee, position)
    if not dist_check["allowed"]:
        return {
            "success": False,
            "final_ee_position": None,
            "error": dist_check["error"],
        }

    # Execute
    result = await sim_connector.move_to(arm, position, orientation, speed)

    # Post-check state
    new_state = await sim_connector.get_state(arm)
    state_manager.record(new_state)
    post = safety.check_state(new_state[arm])
    if post["emergency_stop"]:
        return {
            "success": False,
            "final_ee_position": None,
            "error": f"EMERGENCY STOP: {post['reason']}",
        }

    return result


@mcp.tool()
async def move_joints(
    arm: str, positions: list[float], speed: str = "normal"
) -> dict:
    """Move arm to specified joint positions.

    Args:
        arm: Which arm to move. "left" or "right".
        positions: Target joint positions (7 values in radians).
        speed: Movement speed. One of "slow", "normal", "fast".
    """
    # Pre-check
    check = safety.check_move_joints(arm, positions)
    if not check["allowed"]:
        return {
            "success": False,
            "final_joint_positions": None,
            "error": check["error"],
        }

    # Execute
    result = await sim_connector.move_joints(arm, positions, speed)

    # Post-check state
    new_state = await sim_connector.get_state(arm)
    state_manager.record(new_state)
    post = safety.check_state(new_state[arm])
    if post["emergency_stop"]:
        return {
            "success": False,
            "final_joint_positions": None,
            "error": f"EMERGENCY STOP: {post['reason']}",
        }

    return result


@mcp.tool()
async def home(arm: str = "both") -> dict:
    """Return arm(s) to home position.

    Args:
        arm: Which arm to home. One of "left", "right", "both".
    """
    result = await sim_connector.home(arm)
    state = await sim_connector.get_state("both" if arm == "both" else arm)
    state_manager.record(state)

    # Post-check state
    arms_to_check = ["left", "right"] if arm == "both" else [arm]
    for a in arms_to_check:
        post = safety.check_state(state[a])
        if post["emergency_stop"]:
            return {"success": False, "error": f"EMERGENCY STOP: {post['reason']}"}

    return result


# --- Gripper ---


@mcp.tool()
async def grasp(arm: str, width: float = 0.0, force: float = 40.0) -> dict:
    """Close gripper to grasp an object.

    Args:
        arm: Which arm's gripper. "left" or "right".
        width: Target gripper width in meters.
        force: Grasp force in Newtons.
    """
    result = await sim_connector.grasp(arm, width, force)

    # Post-check state
    new_state = await sim_connector.get_state(arm)
    state_manager.record(new_state)
    post = safety.check_state(new_state[arm])
    if post["emergency_stop"]:
        return {
            "success": False,
            "final_width": None,
            "object_detected": False,
            "error": f"EMERGENCY STOP: {post['reason']}",
        }

    return result


@mcp.tool()
async def release(arm: str, width: float = 0.08) -> dict:
    """Open gripper to release an object.

    Args:
        arm: Which arm's gripper. "left" or "right".
        width: Target gripper opening width in meters.
    """
    result = await sim_connector.release(arm, width)

    # Post-check state
    new_state = await sim_connector.get_state(arm)
    state_manager.record(new_state)
    post = safety.check_state(new_state[arm])
    if post["emergency_stop"]:
        return {
            "success": False,
            "final_width": None,
            "error": f"EMERGENCY STOP: {post['reason']}",
        }

    return result


# --- Scene ---


@mcp.tool()
async def reset_scene(scenario: str = "") -> dict:
    """Reset the simulation scene.

    Args:
        scenario: Optional scenario name to load.
    """
    return await sim_connector.reset_scene(scenario)


@mcp.tool()
async def step_sim(steps: int = 1) -> dict:
    """Step the simulation forward.

    Args:
        steps: Number of simulation steps to advance.
    """
    return await sim_connector.step_sim(steps)


if __name__ == "__main__":
    mcp.run()
