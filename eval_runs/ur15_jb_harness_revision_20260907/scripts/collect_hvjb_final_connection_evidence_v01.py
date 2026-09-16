# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse original-frame extraction for late HVJB connection observations [s]."""

import collect_hvjb_plate_evidence_v01 as reuse

if __name__ == "__main__":
    reuse.REFERENCE = reuse.ROOT / "references/hvjb_final_connections_20260916"
    reuse.OUTPUT = reuse.ROOT / "data/hvjb_final_connection_evidence_v01.json"
    reuse.TIMES = (212, 220, 228, 236, 238, 240, 242, 244, 246, 248, 250, 252, 254, 256, 258, 260, 264)
    reuse.main()
