# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse guarded full-frame extraction at additional header-routing times [s]."""

import collect_hvjb_plate_evidence_v01 as reuse

if __name__ == "__main__":
    reuse.REFERENCE = reuse.ROOT / "references/hvjb_header_sequence_20260916"
    reuse.OUTPUT = reuse.ROOT / "data/hvjb_header_evidence_v01.json"
    reuse.TIMES = (20, 26, 29, 60, 80, 130, 137, 139, 167, 168, 169, 171, 172, 174, 176, 180, 184, 188, 192)
    reuse.main()
