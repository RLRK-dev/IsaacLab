# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""(d2) metrics -- ONE definition, used identically on the recording and on the env.

WHY A SHARED MODULE (%10 C-3). The 4.16mm figure that the P1 bar keys off was measured on the RECORDING. If
the env is measured with even a slightly different formula -- a different segment, a different clip centre, 3D
vs horizontal, or a different groove Z -- the comparison is a cross-mode transplant, which is the class that
produced the 10x misread in B2 (ERRATUM-A). So the recording and the env go through the SAME function, and the
function is validated by reproducing the recording's own number before it is ever pointed at the env.

⚠ GROOVE Z: the route scene floats its clips 20mm above the table, so the groove centre is
``ROUTE_GROOVE_Z = 0.829`` (route_env_config.py:144), NOT ``task_config.GROOVE_CENTER_Z = 0.809``. Using the
latter puts every distance 20mm out. (%10 CRIT-1; %9 independently measured the golden's seated plane at 829.0mm.)

⚠ THE BAR IS BEHAVIOURAL, NOT A VALUE MATCH (%12 MED-2). 4.16mm is the PRODUCER build's value; the env is a
different build -- that difference is the very premise of FORK-1 -- so requiring the env to reproduce 4.16mm
would false-FAIL a working pin. The bar is BOUNDED (<= P1_BOUND_MM) and NON-DIVERGING (not monotonically
increasing). Its discriminating power is established by requiring arm A (no pin) to FAIL the same bar in the
same leg (%10 C-2) -- an instrument that only ever passes is not an instrument.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
for _p in ("thread_isaac_lab", "thread_isaac_lab/envs", "thread_isaac_lab/configs"):
    _d = str(_REPO / _p)
    if _d not in sys.path:
        sys.path.insert(0, _d)

import route_env_config as rc  # noqa: E402
import task_config as tc  # noqa: E402

# The C1 seat, measured (NOT inferred): the producer's recording pins eq 27 on newton body 55; the capture's
# eq_identity table shows the 40 connect-to-world eqs are contiguous 0..39 with obj1 strictly +1 monotone
# (eq i -> mjc body i+29), and mjc = newton + 1 (worldbody at 0). All three close on segment 27.
SEAT_SEG = 27

P1_BOUND_MM = 10.0  # bounded: a held seat stays well inside this (recording: 4.12-4.22mm)
P1_SLOPE_TOL_MM_PER_KSTEP = 1.0  # non-diverging: no sustained monotone escape (pin-less runs to 52.87mm)


def c1_groove_center(clip_y: float = 0.150) -> np.ndarray:
    """C1 groove centre [m]. C1 is an ODD clip (x = 0.35); Z floats 20mm above the table."""
    return np.array([tc.CLIP_X_ODD, float(clip_y), rc.ROUTE_GROOVE_Z], dtype=np.float64)


def seat_distance_mm(cable_xyz: np.ndarray, clip_y: float = 0.150, seg: int = SEAT_SEG) -> np.ndarray:
    """⚠ CONFOUNDED -- telemetry only. Node-to-groove-centre 3D distance. DO NOT build a bar on this.

    Kept because it is what the env's ``_seat_metrics`` computes, so the (d2) run can show the broken instrument
    and the correct one side by side. But it charges CABLE-AXIS NODE PLACEMENT as if it were seating error:

      * the cable has 40 nodes at ~14.64mm spacing, so |dy| has a quantization floor of +-7.32mm (%12);
      * measured on the canonical golden's final frame, the 4.16mm "lateral" is dx = -0.15mm and dy = -4.16mm --
        i.e. ENTIRELY the y-offset of whichever node happened to be nearest, with x essentially dead-centre;
      * and the cable RADIUS is 4mm (task_config.py:137), so a 4.16mm CENTRE offset still leaves the SURFACE
        embedded in the groove wall -- the producer measures ``cable_c1_final_dist_mm = -0.553mm`` (%10).

    So a 3mm bar on this quantity is finer than the resolution of the quantity itself, and it fails a reference
    that is physically seated. Two independent reviewers reached that from opposite directions (quantization;
    surface-vs-centre convention). Use :func:`centerline_offset_mm` or the producer's wall distance instead.
    """
    a = np.asarray(cable_xyz, dtype=np.float64)
    return np.linalg.norm(a[:, int(seg), :] - c1_groove_center(clip_y), axis=1) * 1e3


def centerline_offset_mm(cable_xyz: np.ndarray, clip_y: float = 0.150):
    """Quantization-FREE seating offset: interpolate the cable CENTRELINE at y = C1_Y, measure (|dx|, z_gap).

    Dropping the dy term removes the term that has no physical referent (where a node landed along the axis)
    and keeps the two that do: how far the cable is from the groove in X, and how far in Z. Nothing is loosened
    -- the bar is unchanged; a term with no measurand is simply not charged (%12's fix reaches 81/81 cells with
    the SAME 3mm bar, against 24/81 for the node-based form).

    Returns:
        (dx_mm, z_gap_mm) per frame -- both signed-magnitude in mm.
    """
    a = np.asarray(cable_xyz, dtype=np.float64)
    c1 = c1_groove_center(clip_y)
    y = a[:, :, 1]
    i = np.argmin(np.abs(y - c1[1]), axis=1)
    f = np.arange(a.shape[0])
    yi = y[f, i]
    j = np.clip(i + np.where(yi < c1[1], 1, -1), 0, a.shape[1] - 1)
    yj = y[f, j]
    denom = np.where(np.abs(yj - yi) < 1e-12, 1.0, yj - yi)
    w = np.where(np.abs(yj - yi) < 1e-12, 0.0, (c1[1] - yi) / denom)
    x = a[f, i, 0] + w * (a[f, j, 0] - a[f, i, 0])
    z = a[f, i, 2] + w * (a[f, j, 2] - a[f, i, 2])
    return np.abs(x - c1[0]) * 1e3, (z - c1[2]) * 1e3


def weld_hold_mm(cable_xyz: np.ndarray, onset: int, seg: int = SEAT_SEG) -> np.ndarray:
    """Does the WELDED segment stay where it was welded? [mm from its anchor, per frame]

    This is the cleanest P1 question, and it needs no groove convention at all: the pin welds segment ``seg`` to
    a world anchor at the onset frame, so a working pin keeps that segment AT the anchor. It tracks one fixed
    node throughout, so cable-axis quantization cannot enter. A pin that never fired lets the segment walk away.
    """
    a = np.asarray(cable_xyz, dtype=np.float64)
    return np.linalg.norm(a[:, int(seg), :] - a[int(onset), int(seg), :], axis=1) * 1e3


def p1_verdict(d_mm: np.ndarray, onset: int) -> dict:
    """Is the seat HELD? Bounded and non-diverging over the post-onset window (NOT 'equals 4.16mm')."""
    post = np.asarray(d_mm, dtype=np.float64)[int(onset) :]
    if post.size < 2:
        return {"held": False, "why": "post-onset window is empty"}
    x = np.arange(post.size, dtype=np.float64)
    slope = float(np.polyfit(x, post, 1)[0]) * 1000.0  # mm per 1000 frames
    bounded = bool(post.max() <= P1_BOUND_MM)
    non_div = bool(slope <= P1_SLOPE_TOL_MM_PER_KSTEP)
    return {
        "held": bool(bounded and non_div),
        "max_mm": round(float(post.max()), 3),
        "median_mm": round(float(np.median(post)), 3),
        "final_mm": round(float(post[-1]), 3),
        "slope_mm_per_kframe": round(slope, 3),
        "bounded": bounded,
        "non_diverging": non_div,
        "bars": {"bound_mm": P1_BOUND_MM, "slope_tol": P1_SLOPE_TOL_MM_PER_KSTEP},
    }


def articulation(cable_xyz: np.ndarray) -> dict:
    """Is the chain ALIVE, or did the weld FREEZE it? (%9 -- an INPUT to the video judgment, never a verdict.)

    A weld can convert bad physics into good numbers: it may not have FIXED the divergence but HIDDEN it, by
    rigidifying the chain. That leaves a numeric footprint -- the joints stop working. This reports the footprint
    so the video analyst knows WHERE to look. It does not, and must not, decide anything: whether the pin fixed
    or hid the failure is settled on video, by Rs (motion-bearing verdicts require the visual leg).

    ⚠ MEASURE THE JOINTS, NOT THE POSITIONS. The first version of this function averaged absolute segment
    displacement -- which a rigidly-frozen chain being dragged across the table would sail through, because the
    segments still MOVE, they just stop moving RELATIVE TO EACH OTHER. That is the same confound %12 found in the
    bend-plane metric (angle-to-world-X cannot separate roll from yaw; a yawing vertical plane fakes a roll).
    So the quantity here is the DISCRETE CURVATURE -- the angle between consecutive segment vectors -- whose
    time-variation is invariant to any rigid translation or rotation of the whole cable. A frozen chain scores
    zero no matter how it is carried.
    """
    a = np.asarray(cable_xyz, dtype=np.float64)
    v = np.diff(a, axis=1)  # [F, S-1, 3] segment vectors
    v /= np.linalg.norm(v, axis=2, keepdims=True) + 1e-12
    dot = np.clip(np.einsum("fij,fij->fi", v[:, :-1, :], v[:, 1:, :]), -1.0, 1.0)
    kappa = np.arccos(dot)  # [F, S-2] joint (bend) angles -- rigid-motion INVARIANT
    d_kappa = np.abs(np.diff(kappa, axis=0))  # per-frame joint articulation [rad]
    per_joint = d_kappa.mean(axis=0)  # [S-2] mean articulation per joint
    j = SEAT_SEG - 1  # the joint nearest the welded segment
    near = per_joint[max(j - 3, 0) : j + 4]
    far = np.concatenate([per_joint[: max(j - 6, 0)], per_joint[j + 7 :]])
    return {
        "metric": "mean |d(joint angle)|/frame [rad] -- invariant to rigid motion of the whole cable",
        "mean_articulation": round(float(per_joint.mean()), 6),
        "near_seat": round(float(near.mean()), 6),
        "far_from_seat": round(float(far.mean()), 6) if far.size else None,
        "near_over_far": (round(float(near.mean() / far.mean()), 4) if far.size and far.mean() > 1e-12 else None),
        "note": "INPUT to the video judgment, not a verdict. A collapse here = the footprint of HIDING, not fixing.",
    }
