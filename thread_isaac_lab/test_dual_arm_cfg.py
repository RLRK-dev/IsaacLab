#!/usr/bin/env python3
"""
Test script: Validate dual arm configuration
Prints configuration summary without requiring Isaac Sim
"""

from __future__ import annotations


def print_dual_arm_config():
    """Print dual arm configuration summary (standalone, no Isaac Sim required)."""

    # Constants from dual_arm_cfg.py
    ARM_SEPARATION = 0.7
    TABLE_HEIGHT = 0.75

    print("=" * 70)
    print("THREAD DUAL ARM SCENE CONFIGURATION")
    print("=" * 70)

    print(f"\n[Environment]")
    print(f"  Num environments: 256")
    print(f"  Environment spacing: 3.0m (larger for dual arm)")

    print(f"\n[Robots]")
    print(f"  Left arm:")
    print(f"    Prim path: {{ENV_REGEX_NS}}/Robot_Left")
    print(f"    Position: ({-ARM_SEPARATION/2:.2f}, 0.00, 0.00)")
    print(f"    Rotation: 45deg toward center (w=0.924, z=0.383)")
    print(f"    Joint 1 initial: +0.4 rad (toward center)")
    print(f"  Right arm:")
    print(f"    Prim path: {{ENV_REGEX_NS}}/Robot_Right")
    print(f"    Position: ({ARM_SEPARATION/2:.2f}, 0.00, 0.00)")
    print(f"    Rotation: -45deg toward center (w=0.924, z=-0.383)")
    print(f"    Joint 1 initial: -0.4 rad (toward center)")
    print(f"  Arm separation: {ARM_SEPARATION}m")

    print(f"\n[Table]")
    print(f"  Prim path: {{ENV_REGEX_NS}}/Table")
    print(f"  Size: 1.0m x 0.8m x 0.02m")
    print(f"  Position: (0.4, 0.0, {TABLE_HEIGHT - 0.01:.2f})")
    print(f"  Surface height: {TABLE_HEIGHT}m")

    print(f"\n[Hook]")
    print(f"  Position: (0.4, 0.0, {TABLE_HEIGHT + 0.13:.2f}) - 13cm above table")

    print(f"\n[Cable]")
    print(f"  Position: (0.4, -0.1, {TABLE_HEIGHT + 0.03:.2f}) - on table, slightly left")

    print(f"\n[Cameras]")
    print(f"  Overhead camera:")
    print(f"    Prim path: {{ENV_REGEX_NS}}/OverheadCamera")
    print(f"    Resolution: 640x480")
    print(f"    Position: (0.4, 0.0, 1.2) - 1.2m above table center")
    print(f"    Orientation: Looking straight down (-Z)")
    print(f"    Focal length: 18mm (wide angle)")
    print(f"    FOV: ~60 degrees")

    print(f"\n  Left wrist camera:")
    print(f"    Prim path: {{ENV_REGEX_NS}}/Robot_Left/panda_hand/LeftWristCamera")
    print(f"    Resolution: 224x224")
    print(f"    Mount offset: (0.05, 0.0, 0.04) from hand center")
    print(f"    Focal length: 12mm (close-up)")
    print(f"    Clipping: 0.01m - 2.0m")

    print(f"\n  Right wrist camera:")
    print(f"    Prim path: {{ENV_REGEX_NS}}/Robot_Right/panda_hand/RightWristCamera")
    print(f"    Resolution: 224x224")
    print(f"    Mount offset: (0.05, 0.0, 0.04) from hand center")
    print(f"    Focal length: 12mm (close-up)")
    print(f"    Clipping: 0.01m - 2.0m")

    # Calculate camera intrinsics
    print(f"\n[Camera Intrinsics]")

    cameras = [
        ("Overhead", 640, 480, 18.0, 20.955),
        ("Left Wrist", 224, 224, 12.0, 15.0),
        ("Right Wrist", 224, 224, 12.0, 15.0),
    ]

    for name, width, height, focal_length, horizontal_aperture in cameras:
        fx = focal_length * width / horizontal_aperture
        fy = fx  # Square pixels
        cx = width / 2.0
        cy = height / 2.0
        print(f"  {name}: fx={fx:.1f}, fy={fy:.1f}, cx={cx:.1f}, cy={cy:.1f}")

    print(f"\n[Contact Sensors]")
    print(f"  Left gripper: {{ENV_REGEX_NS}}/Robot_Left/panda_leftfinger")
    print(f"  Right gripper: {{ENV_REGEX_NS}}/Robot_Right/panda_leftfinger")
    print(f"  Filter: Cable.* objects")

    print(f"\n[Workspace Layout - Top View]")
    print("""
                        Table (1.0m x 0.8m)
                    +-------------------------+
                    |                         |
        Robot_Left  |   Cable         Hook    |  Robot_Right
             *      |     o            o      |      *
             |\\     |                         |     /|
             | \\    +-------------------------+    / |
             |  \\             ^                   /  |
             +---\\           0.7m               /---+
                  \\           |                /
                   \\__________+_______________/
                         workspace center
    """)

    print("=" * 70)
    print("[完了] 双腕構成の設定確認完了")
    print("=" * 70)


if __name__ == "__main__":
    print_dual_arm_config()
