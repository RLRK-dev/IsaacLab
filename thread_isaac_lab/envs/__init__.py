"""
THREAD Environment Definitions for Isaac Lab
=============================================

This module contains the Isaac Lab environment implementations
for the THREAD cable manipulation tasks.

Available Environments:
    - HookHangingEnv: Single-arm hook hanging task
    - HookHangingEnvCfg: Configuration for hook hanging

Asset Configurations:
    - FrankaPandaCfg: Franka Panda robot configuration
    - CableSegmentedCfg: Segmented cable (DLO) configuration
    - SimpleHookCfg: Hook target configuration
    - TableCfg: Workspace table configuration
"""

from .assets_cfg import (
    FrankaPandaCfg,
    DualFrankaCfg,
    CableAssetCfg,
    CableSegmentedCfg,
    SimpleHookCfg,
    HookCfg,
    TableCfg,
    OverheadCameraCfg,
    WristCameraCfg,
    HookHangingSceneCfg,
    HookHangingSceneCfgSingleArm,
)

from .hook_hanging_env import (
    HookHangingEnv,
    HookHangingEnvCfg,
)

from .dual_arm_flex_env_cfg import (
    DualArmFlexCableSceneCfg,
    NUM_CABLE_SEGMENTS,
    CABLE_SEGMENT_LENGTH,
    CABLE_TOTAL_LENGTH,
    TABLE_HEIGHT,
    TASK_STATE_DIM,
)

from .flexible_cable_utils import (
    create_flexible_cable,
    create_l_hook,
)

from .dual_arm_cfg import (
    LeftFrankaCfg,
    RightFrankaCfg,
    DualArmSceneCfg,
    DualArmTableCfg,
    SEGMENTED_CABLE_USD,
)

__all__ = [
    # Robot configs
    "FrankaPandaCfg",
    "DualFrankaCfg",
    # Object configs
    "CableAssetCfg",
    "CableSegmentedCfg",
    "SimpleHookCfg",
    "HookCfg",
    "TableCfg",
    # Sensor configs
    "OverheadCameraCfg",
    "WristCameraCfg",
    # Scene configs
    "HookHangingSceneCfg",
    "HookHangingSceneCfgSingleArm",
    "DualArmFlexCableSceneCfg",
    # Flexible cable utils
    "create_flexible_cable",
    "create_l_hook",
    "NUM_CABLE_SEGMENTS",
    "CABLE_SEGMENT_LENGTH",
    "CABLE_TOTAL_LENGTH",
    "TABLE_HEIGHT",
    "TASK_STATE_DIM",
    # Environment
    "HookHangingEnv",
    "HookHangingEnvCfg",
    # Dual Arm
    "LeftFrankaCfg",
    "RightFrankaCfg",
    "DualArmSceneCfg",
    "DualArmTableCfg",
    "SEGMENTED_CABLE_USD",
]
