#!/usr/bin/env python3
"""
Check robot workspace and cable position overlap.
"""

import math

# Robot positions
LEFT_ROBOT_BASE = (0.0, -0.30, 0.75)
RIGHT_ROBOT_BASE = (0.0, 0.30, 0.75)

# Franka Panda specifications
FRANKA_MAX_REACH = 0.855  # meters
FRANKA_EFFECTIVE_REACH = 0.75  # conservative estimate

# Table
TABLE_CENTER = (0.4, 0.0, 0.75)
TABLE_SIZE = (1.0, 0.8)  # X, Y

# Cable specifications (from segmented_cable.usd)
CABLE_LENGTH = 0.5  # 10 segments * 0.05m
CABLE_SEGMENT_COUNT = 10

def distance_2d(p1, p2):
    """Calculate 2D distance (XY plane)."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def distance_3d(p1, p2):
    """Calculate 3D distance."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)

def is_reachable(robot_base, target, max_reach):
    """Check if target is reachable by robot."""
    dist = distance_3d(robot_base, target)
    return dist <= max_reach, dist

def print_workspace_analysis():
    print("=" * 70)
    print("WORKSPACE ANALYSIS")
    print("=" * 70)

    print("\n[Robot Positions]")
    print(f"  Left robot:  X={LEFT_ROBOT_BASE[0]:.2f}, Y={LEFT_ROBOT_BASE[1]:.2f}, Z={LEFT_ROBOT_BASE[2]:.2f}")
    print(f"  Right robot: X={RIGHT_ROBOT_BASE[0]:.2f}, Y={RIGHT_ROBOT_BASE[1]:.2f}, Z={RIGHT_ROBOT_BASE[2]:.2f}")
    print(f"  Maximum reach: {FRANKA_MAX_REACH}m")
    print(f"  Effective reach: {FRANKA_EFFECTIVE_REACH}m")

    print("\n[Robot Workspace Bounds (2D projection at table height)]")
    # Left robot workspace
    left_x_min = LEFT_ROBOT_BASE[0] - FRANKA_EFFECTIVE_REACH
    left_x_max = LEFT_ROBOT_BASE[0] + FRANKA_EFFECTIVE_REACH
    left_y_min = LEFT_ROBOT_BASE[1] - FRANKA_EFFECTIVE_REACH
    left_y_max = LEFT_ROBOT_BASE[1] + FRANKA_EFFECTIVE_REACH
    print(f"  Left robot:  X=[{left_x_min:.2f}, {left_x_max:.2f}], Y=[{left_y_min:.2f}, {left_y_max:.2f}]")

    # Right robot workspace
    right_x_min = RIGHT_ROBOT_BASE[0] - FRANKA_EFFECTIVE_REACH
    right_x_max = RIGHT_ROBOT_BASE[0] + FRANKA_EFFECTIVE_REACH
    right_y_min = RIGHT_ROBOT_BASE[1] - FRANKA_EFFECTIVE_REACH
    right_y_max = RIGHT_ROBOT_BASE[1] + FRANKA_EFFECTIVE_REACH
    print(f"  Right robot: X=[{right_x_min:.2f}, {right_x_max:.2f}], Y=[{right_y_min:.2f}, {right_y_max:.2f}]")

    # Overlap region
    overlap_x_min = max(left_x_min, right_x_min)
    overlap_x_max = min(left_x_max, right_x_max)
    overlap_y_min = max(left_y_min, right_y_min)
    overlap_y_max = min(left_y_max, right_y_max)

    print(f"\n[Workspace Overlap Region]")
    if overlap_x_min < overlap_x_max and overlap_y_min < overlap_y_max:
        print(f"  X=[{overlap_x_min:.2f}, {overlap_x_max:.2f}]")
        print(f"  Y=[{overlap_y_min:.2f}, {overlap_y_max:.2f}]")
        overlap_center = ((overlap_x_min + overlap_x_max) / 2, (overlap_y_min + overlap_y_max) / 2)
        print(f"  Center: ({overlap_center[0]:.2f}, {overlap_center[1]:.2f})")
    else:
        print("  No overlap!")

    print("\n" + "=" * 70)
    print("CABLE POSITION RECOMMENDATIONS")
    print("=" * 70)

    # Cable should span from left robot's reach to right robot's reach
    # For dual-arm grasping, each robot grabs one end

    # Ideal cable position: centered between robots, within both reach
    # Left end should be reachable by left robot
    # Right end should be reachable by right robot

    # Best X position: in front of robots where both can reach
    # The table center is at X=0.4, which is good
    best_x = 0.35  # Slightly closer to robots

    # Cable should span Y direction
    # Left end at Y close to 0 (reachable by both, but mainly left)
    # Right end at Y close to 0 (reachable by both, but mainly right)

    # For robot at Y=-0.30 to reach forward (X=0.35), max Y reach is limited
    # Distance from left robot (0, -0.30) to (0.35, Y):
    # sqrt(0.35² + (Y+0.30)²) <= 0.75
    # (Y+0.30)² <= 0.75² - 0.35² = 0.44
    # Y+0.30 <= 0.66
    # Y <= 0.36

    left_robot_max_y = -0.30 + math.sqrt(FRANKA_EFFECTIVE_REACH**2 - best_x**2)
    left_robot_min_y = -0.30 - math.sqrt(FRANKA_EFFECTIVE_REACH**2 - best_x**2)

    right_robot_max_y = 0.30 + math.sqrt(FRANKA_EFFECTIVE_REACH**2 - best_x**2)
    right_robot_min_y = 0.30 - math.sqrt(FRANKA_EFFECTIVE_REACH**2 - best_x**2)

    print(f"\n[At X={best_x:.2f}]")
    print(f"  Left robot Y-reach:  [{left_robot_min_y:.2f}, {left_robot_max_y:.2f}]")
    print(f"  Right robot Y-reach: [{right_robot_min_y:.2f}, {right_robot_max_y:.2f}]")

    # Ideal cable placement
    # Left end should be at Y that left robot can easily reach
    # Right end should be at Y that right robot can easily reach
    # Cable length is 0.5m

    # Option 1: Cable centered at Y=0
    cable_center_y_opt1 = 0.0
    cable_left_end_y_opt1 = cable_center_y_opt1 - CABLE_LENGTH / 2
    cable_right_end_y_opt1 = cable_center_y_opt1 + CABLE_LENGTH / 2

    print(f"\n[Option 1: Cable centered at Y=0.0]")
    print(f"  Cable spans: Y=[{cable_left_end_y_opt1:.2f}, {cable_right_end_y_opt1:.2f}]")

    left_end_pos = (best_x, cable_left_end_y_opt1, 0.77)
    right_end_pos = (best_x, cable_right_end_y_opt1, 0.77)

    left_reach_left, left_dist_left = is_reachable(LEFT_ROBOT_BASE, left_end_pos, FRANKA_EFFECTIVE_REACH)
    right_reach_right, right_dist_right = is_reachable(RIGHT_ROBOT_BASE, right_end_pos, FRANKA_EFFECTIVE_REACH)

    print(f"  Left end ({left_end_pos[0]:.2f}, {left_end_pos[1]:.2f}, {left_end_pos[2]:.2f}):")
    print(f"    Distance from left robot: {left_dist_left:.3f}m - {'✓ Reachable' if left_reach_left else '✗ NOT reachable'}")
    print(f"  Right end ({right_end_pos[0]:.2f}, {right_end_pos[1]:.2f}, {right_end_pos[2]:.2f}):")
    print(f"    Distance from right robot: {right_dist_right:.3f}m - {'✓ Reachable' if right_reach_right else '✗ NOT reachable'}")

    # Option 2: Closer to robots
    best_x2 = 0.30
    print(f"\n[Option 2: Cable at X={best_x2:.2f}, centered at Y=0.0]")
    left_end_pos2 = (best_x2, cable_left_end_y_opt1, 0.77)
    right_end_pos2 = (best_x2, cable_right_end_y_opt1, 0.77)

    left_reach_left2, left_dist_left2 = is_reachable(LEFT_ROBOT_BASE, left_end_pos2, FRANKA_EFFECTIVE_REACH)
    right_reach_right2, right_dist_right2 = is_reachable(RIGHT_ROBOT_BASE, right_end_pos2, FRANKA_EFFECTIVE_REACH)

    print(f"  Left end ({left_end_pos2[0]:.2f}, {left_end_pos2[1]:.2f}, {left_end_pos2[2]:.2f}):")
    print(f"    Distance from left robot: {left_dist_left2:.3f}m - {'✓ Reachable' if left_reach_left2 else '✗ NOT reachable'}")
    print(f"  Right end ({right_end_pos2[0]:.2f}, {right_end_pos2[1]:.2f}, {right_end_pos2[2]:.2f}):")
    print(f"    Distance from right robot: {right_dist_right2:.3f}m - {'✓ Reachable' if right_reach_right2 else '✗ NOT reachable'}")

    print("\n" + "=" * 70)
    print("RECOMMENDED CONFIGURATION")
    print("=" * 70)

    print("""
Cable initial position in dual_arm_cfg.py:

    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.30, 0.0, TABLE_HEIGHT + 0.02),  # Closer to robots, centered
        rot=(0.7071, 0.7071, 0.0, 0.0),  # +90° around X to lie along +Y
    ),

This will place the cable:
- X = 0.30 (closer to robots for better reach)
- Y = 0.0 (centered, spanning -0.25 to +0.25)
- Z = TABLE_HEIGHT + 0.02 (on table surface)
""")

if __name__ == "__main__":
    print_workspace_analysis()
