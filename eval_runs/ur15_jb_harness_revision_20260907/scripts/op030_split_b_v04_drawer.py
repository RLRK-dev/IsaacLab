# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Shared timing for B supply motion overlapping A and the B-to-C transfer [s]."""

import numpy as np

DRAWER_STROKE = 0.340


def drawer_extension(
    times: np.ndarray, *, supply_start: float, return_start: float, duration: float = 2.5
) -> np.ndarray:
    """Return the reused drawer's local X extension [m] at global times [s].

    Args:
        times: Global timeline samples [s].
        supply_start: Start of opening during A work [s].
        return_start: Start of closing after B finishes [s].
        duration: Duration of each complete 0.340 m stroke [s].

    Returns:
        Extension [m] from zero to 0.340 m. Both stroke endpoints have zero
        velocity and acceleration. This defines timing, not a collision result.
    """
    times = np.asarray(times, dtype=float)
    if duration <= 0 or return_start < supply_start + duration:
        raise ValueError("Drawer opening and closing intervals must not overlap")
    if not np.all(np.isfinite(times)) or not np.all(np.isfinite([supply_start, return_start, duration])):
        raise ValueError("Drawer timing must be finite")

    def stopped_weight(start):
        u = np.clip((times - start) / duration, 0.0, 1.0)
        return u**3 * (10.0 - 15.0 * u + 6.0 * u**2)

    return DRAWER_STROKE * (stopped_weight(supply_start) - stopped_weight(return_start))


def drawer_overlap_windows(*, a_start: float, b_start: float, b_stop: float, duration: float = 2.5) -> dict:
    """Describe exact overlapping intervals and required state conditions [s].

    Args:
        a_start: Beginning of A work and B drawer opening [s].
        b_start: First sample of B work, after the drawer is fully open [s].
        b_stop: Final B sample, with both arms parked and both wires seated [s].
        duration: Each opening/closing stroke duration [s].

    Returns:
        Timing metadata for the main timeline and the combined geometry check.
    """
    if duration <= 0 or b_start < a_start + duration or b_stop < b_start:
        raise ValueError("The supply must be open before B begins; return follows B completion")
    return dict(
        supply_start_s=a_start,
        supply_stop_s=a_start + duration,
        return_start_s=b_stop,
        return_stop_s=b_stop + duration,
        stroke_m=DRAWER_STROKE,
        duration_s=duration,
        open_inventory_count=10,
        return_inventory_count=8,
        source_law="Retained stopped quintic drawer motion",
        conditions=[
            "Opening uses B initial parked poses and simultaneous actual A poses",
            "B pickup starts only after the drawer reaches full extension",
            "Closing begins after the two active wire UIDs are seated and both B arms have parked",
            "Only the eight remaining stock UIDs follow the returning supply drawer",
            "Closing is checked with actual pin withdrawal, product transport and C arrival poses",
        ],
        geometry_validation="Separate combined-motion actual-mesh audit required",
    )
