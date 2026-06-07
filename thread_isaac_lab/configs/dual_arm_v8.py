# THREAD Dual Arm v8 Configuration
#
# Key Change: Move cable closer to robots to ensure physical reachability
#
# v7 Problem: Cable at (0.5, 0.0, 0.8) was at 0.824m from robot base
#             Franka reach is 0.855m, leaving only 3.1cm margin
#             This caused EE-Cable distance to plateau at ~0.22m
#
# v8 Solution: Move cable to (0.45, 0.0, 0.7)
#              Distance becomes 0.723m, margin is 13.2cm
#              This should allow PPO to find reaching solutions

"""
Version History:
- v1-v3: Baseline (EE-Cable ~0.4m)
- v4-v5: Extended training (no improvement)
- v6: Closer robots + steeper reward (EE-Cable ~0.26m)
- v7: Even closer robots (EE-Cable ~0.22m, but plateaued due to reach limit)
- v8: Move cable closer (target: EE-Cable < 0.1m)
"""

# =============================================================================
# SCENE CONFIGURATION
# =============================================================================

# Robot positions (keep same as v7)
ARM_X_POS = 0.42      # X position for both arms
ARM_Y_OFFSET = 0.18   # Distance from center on Y-axis

# Cable position (CHANGED from v7)
# v7: (0.5, 0.0, 0.80) - distance 0.824m, margin 3.1cm
# v8: (0.45, 0.0, 0.70) - distance 0.723m, margin 13.2cm
CABLE_X = 0.45
CABLE_Y = 0.0
CABLE_Z = 0.70

# Hook position (adjusted to match cable height)
HOOK_X = 0.0
HOOK_Y = 0.0
HOOK_Z = 0.90  # Lowered from 1.0 to match cable

# =============================================================================
# REWARD CONFIGURATION (same as v7)
# =============================================================================

# Approach reward (exponential decay)
APPROACH_STD = 0.3  # Steeper gradient for close positions (v6: 1.0)

# Close bonus thresholds
CLOSE_THRESHOLD = 0.10      # EE-Cable < 0.1m triggers close_bonus
GRASP_READY_THRESHOLD = 0.05  # EE-Cable < 0.05m triggers grasp_ready_bonus

# Bonus values
CLOSE_BONUS = 3.0           # v7: 3.0 (v6: 2.0)
GRASP_READY_BONUS = 7.0     # v7: 7.0 (v6: 5.0)

# =============================================================================
# EXPECTED RESULTS
# =============================================================================
"""
Physical Analysis:
- Left robot base: (0.42, -0.18, 0)
- Right robot base: (0.42, 0.18, 0)
- Cable: (0.45, 0, 0.70)
- Distance to cable: 0.723m
- Franka reach: 0.855m
- Margin: 0.132m (13.2cm) - SUFFICIENT for reaching

Expected Performance:
- EE-Cable distance: < 0.15m (vs v7's 0.22m)
- Approach success: > 50% (vs v7's 0%)
- If successful, proceed to grasp training
"""
