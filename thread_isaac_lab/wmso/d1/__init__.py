# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""WMSO D1 — skill contracts, executable identity, static policy adapter, and fail-closed harness.

D1 instantiates the D0 §B/§E schema per the banked design
``WMSO_D1_CONTRACTS_ADAPTERS_DESIGN_RSTECHLEAD2_20260718_v4_1_1.md`` (pN IMPLEMENTATION GO
2026-07-19, frozen path set). Scope is read-only contract/identity/adapter/test work over
*existing* checkpoints and sources. It never trains, runs inference, grounds belief at
runtime, or grants offline/closed-loop authority (both are hard-false). D1 exit remains HOLD
until an authoritative training-env schema resolves the learned exemplars.
"""
