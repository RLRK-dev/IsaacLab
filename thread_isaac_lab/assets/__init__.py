"""THREAD Assets Module"""

from .flexible_cable import (
    FlexibleCableCfg,
    create_flexible_cable_usd,
    create_cable_segments_config,
    NUM_SEGMENTS,
    SEGMENT_LENGTH,
    SEGMENT_RADIUS,
    TOTAL_LENGTH,
    SEGMENT_MASS,
)

from .hook_l_shape import (
    HookLShapeCfg,
    create_l_hook_usd,
    HOOK_VERTICAL_LENGTH,
    HOOK_HORIZONTAL_LENGTH,
    HOOK_RADIUS,
)

__all__ = [
    "FlexibleCableCfg",
    "create_flexible_cable_usd",
    "create_cable_segments_config",
    "HookLShapeCfg",
    "create_l_hook_usd",
]
