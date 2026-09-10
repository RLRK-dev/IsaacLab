# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Load the nearby-feeder C bank with explicit M6 output indexing [m, rad, s]."""

from op030_definition import ROOT
from op030_split_c_v04 import BankSequence, digest

BANK = ROOT / "data/op030_split_c_front_indexed_motion_v05.npz"
BANK_SHA256 = "238c6b233871f25c0e95113b0d4d92124a569218ab8a40926773637e1ad96e38"
MESH = ROOT / "data/op030_split_c_front_feeders_v05_meshes.npz"


def build_sequence() -> BankSequence:
    """Expose the verified recorded C states on the native 30 Hz clock [s]."""
    if digest(BANK) != BANK_SHA256:
        raise ValueError("The near-side C bank changed; rebind only after verification")
    return BankSequence(BANK)
