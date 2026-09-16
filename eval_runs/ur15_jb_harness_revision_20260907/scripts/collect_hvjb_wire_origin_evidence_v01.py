# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse original-frame extraction for pre-merge wire observations [s]."""

import collect_hvjb_plate_evidence_v01 as reuse

if __name__ == "__main__":
    reuse.REFERENCE = reuse.ROOT / "references/hvjb_wire_origin_20260916"
    reuse.OUTPUT = reuse.ROOT / "data/hvjb_wire_origin_evidence_v01.json"
    reuse.TIMES = (26, 28, 40, 44, 54, 58)
    reuse.main()
