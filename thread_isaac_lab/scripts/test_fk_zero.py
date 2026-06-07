#!/usr/bin/env python3
"""
Test FK at zero joint configuration.
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
sys.path.insert(0, "/home/rlrk/IsaacLab")

import numpy as np
from thread_isaac_lab.scripts.franka_analytical_ik import forward_kinematics

# Test at zero joints
joints_zero = np.array([0, 0, 0, 0, 0, 0, 0])
T = forward_kinematics(joints_zero)
pos = T[:3, 3]
print(f"Joints (deg): {np.degrees(joints_zero)}")
print(f"FK position: {pos}")
print(f"Expected approximate: x=0.088, y=0, z=(0.333+0.316+0.384+0.107+0.1034)={0.333+0.316+0.384+0.107+0.1034}")

# Test at Franka "ready" position
joints_ready = np.array([0, -np.pi/4, 0, -3*np.pi/4, 0, np.pi/2, np.pi/4])
T2 = forward_kinematics(joints_ready)
pos2 = T2[:3, 3]
print(f"\nReady position joints (deg): {np.degrees(joints_ready)}")
print(f"FK position: {pos2}")

# Manual calculation for zero config
print("\n--- Manual DH calculation ---")
# Link lengths along z when all joints=0
# d1=0.333, d3=0.316, d5=0.384, d7=0.107, dEE=0.1034
# a7 = 0.088 (along x)

# At zero config, all links extend along +Z (base frame)
# But the 0.088 (a7) extends along X
# And there's a -45deg rotation before EE

d_total = 0.333 + 0.316 + 0.384 + 0.107 + 0.1034
print(f"Sum of d values: {d_total}")
print(f"a7 = 0.088")
