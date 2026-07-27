"""The single source for the UR15 cell's constants.

Implements the contract in `P5_UR15_CELL_CONSTANTS_SPEC_20260727.md` §6, with the clip shape from
`P5_UR15_CLIP_DETAIL_DESIGN_20260727.md` §3 / §6.

The rule, from that spec §0:

    drivers do not define constants -- they read them from one module, and that module reads from
    the authoritative source wherever one exists, carrying a value of its own only where none does.

Why this exists: twelve driver files in this directory disagreed on twenty-one constants, ten of
which change the physics.  One pair had the cable at 8 mm across and the other at 10 mm; one had
40 links and the other 32; the clip wall was 70 mm in two files and 26 mm in three.  Neither side
was the correct one -- each was right about what the other got wrong -- so copying one over the
other was never going to work.

  Tier A -- an authoritative source exists.  Imported, never written down here.
  Tier B -- cell-specific, no authoritative source.  Carried here, each tagged with its spec
            section, and none of them invented: every one is adopted from a measurement comment
            already recorded in the drivers.
  Tier C -- run-specific (output path, resolution, choreography, cameras).  Deliberately absent;
            drivers vary these on purpose.

Call `guard()` from a driver to fail loudly if that driver has redefined anything here.
"""

from __future__ import annotations

import ast
import math
import pathlib
import sys

_REPO = "/home/rlrk/IsaacLab"
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from thread_isaac_lab.configs import task_config as _tc  # noqa: E402

# --------------------------------------------------------------------------------------------
# Tier A -- read from the repo SSOT.  Do not replace any of these with a literal.
# --------------------------------------------------------------------------------------------

TABLE_TOP = _tc.TABLE_HEIGHT                    # task_config.py:20
CABLE_R = _tc.CABLE_RADIUS                      # task_config.py:137
CABLE_N = _tc.CABLE_SEGMENTS                    # task_config.py:135
CABLE_SEG = _tc.CABLE_SEG_LEN                   # task_config.py:136 -- the variable, not the
                                                # comment the spec §3 cited; same value, and it
                                                # cannot drift away from its own source
GRIP_HALF_SPAN = _tc.GRIP_HALF_SPAN             # task_config.py:235
CLIP_BASE_HEIGHT = _tc.CLIP_BASE_HEIGHT         # task_config.py:91
GROOVE_CENTER_Z = _tc.GROOVE_CENTER_Z           # task_config.py:226 == TABLE + 0.009

# Clip contact, spec §6 of the clip design: Newton's (ke, kd) map to MuJoCo's NEGATIVE solref form,
# and the clip is a static geom so it takes the same friction triple as the table.
CLIP_SOLREF = (-_tc.MUJOCO_CONTACT_KE, -_tc.MUJOCO_CONTACT_KD)     # task_config.py:168-169
CLIP_FRICTION = tuple(_tc.MUJOCO_CABLE_TABLE_FRICTION)             # task_config.py:180
CLIP_COLLIDE = True    # clip design §6-A: newton_skill_env_base.py:1908 / :1925 are unconditional

_ENV_BASE = pathlib.Path(_REPO, "thread_isaac_lab/envs/newton_skill_env_base.py")


def _clip_parts_from_source():
    """Read `_v_groove_clip_parts` out of the env source without importing it.

    The module itself cannot be imported here -- it pulls in `isaaclab_physx`, which this venv does
    not have -- so take the literal off the syntax tree instead of copying it.  A copy is what put
    a 10 mm mouth in one file and a 14 mm mouth in another.
    """
    tree = ast.parse(_ENV_BASE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "_v_groove_clip_parts" for t in node.targets):
            return [tuple(p) for p in ast.literal_eval(node.value)]
    raise RuntimeError(f"_v_groove_clip_parts is no longer in {_ENV_BASE}; it moved or was renamed")


def _rotate_90(parts):
    """The env's groove runs along y and this cell's runs along x, so turn it a quarter turn.

    Clip design §3: (dx, dy) -> (-dy, dx), (hx, hy) -> (hy, hx), z untouched.  Exact for
    axis-aligned boxes, and it introduces no new number -- it is the same clip, turned.
    """
    return [(-dy, dx, dz, hy, hx, hz) for dx, dy, dz, hx, hy, hz in parts]


CLIP_PARTS = _rotate_90(_clip_parts_from_source())

# What the clip design §3 says the turned table should be.  Cross-checked rather than copied: if
# the env source changes shape, or if the spec is revised, this disagrees instead of going quiet.
_CLIP_PARTS_PER_SPEC = [
    (0, 0, 0.0025, 0.015, 0.020, 0.0025),
    (0, -0.009, 0.0125, 0.015, 0.0015, 0.0075),
    (0, +0.009, 0.0125, 0.015, 0.0015, 0.0075),
    (0, -0.013, 0.025, 0.015, 0.002, 0.005),
    (0, +0.013, 0.025, 0.015, 0.002, 0.005),
]

# --------------------------------------------------------------------------------------------
# Tier B -- no authoritative source; the spec carries these.  Section numbers are its §4.
# --------------------------------------------------------------------------------------------

SHOULDER_HEIGHT = 0.37 + 0.58 * 2.0     # spec §4 -- all five driver files already agreed
YOKE_SPREAD = 0.40                      # spec §4 -- "0.22/45deg made the two arms interleave at an
TILT = math.pi / 2.0 - math.radians(20.0)  #          88 mm span; 0.40/20deg clears the rest row
                                        #            and both clips" (measured, and measured as a
                                        #            pair, so the two cannot be separated)
TABLE_HX, TABLE_HY = 0.70, 0.20         # spec §4 -- ⚠ weak grounds, and spec §7 asked whether p4
                                        #            had better: it does not.  The driver line
                                        #            carries no measurement comment at all.
REST_Y = 0.28                           # spec §4
REST_X = (-0.34, -0.14, 0.24)           # spec §4 -- "saddles kept clear of both 88 mm grasp spans"
REST_TOP = TABLE_TOP + 0.150            # spec §4 -- "at +0.060 the open fingers press into the
                                        #            table".  ⚠ p4's own gripper-only measurement
                                        #            (36 mm of reach below the cable with the
                                        #            fingers open) does not reproduce that, so the
                                        #            note may have been seeing the wrist above the
                                        #            gripper.  Unresolved; see
                                        #            P4_FINGER_REACH_BELOW_CABLE_20260727.md §4.

# Arm servo -- the spec names these but explicitly declines to judge their values; they belong to
# the arm-control court.  Carried here only so drivers stop each keeping their own copy.
ARMATURE, DAMP = 0.1, 1.0               # spec §4
KP_ARM, KP_WRI, KVR = 10000.0, 1200.0, 0.06   # spec §4

# Finger commands -- the spec deliberately does NOT freeze these ("the measuring lane is moving
# them"), so this module reads the latest banked values rather than fixing them.
CLAMP, HALF, OPEN = 236, 214, 18        # spec §4, latest banked (ur15_steps.py:97)

# ⛔ Not settled.  The clip design §4 makes float_z follow from a seat height that depends on a
# step-table decision p5 has not made: whether the fingers open while still down at the seat.
# Touching this raises rather than silently supplying a number.
_FLOAT_Z_UNSET = ("float_z is not settled: clip design §4 derives it from the seat height, and "
                  "P4_FINGER_REACH_BELOW_CABLE_20260727.md §3 shows that height depends on "
                  "whether STEP 8 opens the fingers at the seat (16.0 mm if not, 35.7 mm if so). "
                  "That is p5's decision, not this module's default.")


def float_z():
    """Height the whole clip is lifted above the table [m].  Raises until p5 settles it."""
    raise NotImplementedError(_FLOAT_Z_UNSET)


def seat_z(float_z_m: float) -> float:
    """World z at which the cable centre rests, for a clip floated this far [m].

    Clip design §4: seat = TABLE + float_z + 9.0 mm, where 9.0 is the 5 mm base plate plus the
    4 mm cable radius.  Both come from Tier A, so the 9.0 is not written down here either.
    """
    return TABLE_TOP + float_z_m + CLIP_BASE_HEIGHT + CABLE_R


# --------------------------------------------------------------------------------------------
# Guard -- spec §6.4, in the form p0's pre-implementation review asked for: one AST pass that
# catches BOTH a driver redefining a name AND a value drifting away from its source.  Byte hashes
# are not a gate here; they only tell you something changed, not whether it still agrees.
# --------------------------------------------------------------------------------------------

_OWNED = {n for n in globals() if n.isupper() and not n.startswith("_")}


def _module_level_assignments(path):
    """Every name bound at module level in `path`, by syntax tree rather than by grep.

    grep misses tuple targets -- and tuple targets are exactly how these drivers wrote the
    constants that disagreed (`GROOVE_W, CLIP_H = 0.016, 0.026`).
    """
    names = {}
    tree = ast.parse(pathlib.Path(path).read_text())
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) else [])
        for t in targets:
            for leaf in ast.walk(t):
                if isinstance(leaf, ast.Name):
                    names[leaf.id] = node.lineno
    return names


def guard(driver_path, strict=True):
    """Fail if `driver_path` redefines anything this module owns.

    Returns the list of offending (name, line).  With strict=True a non-empty list raises, so a
    driver cannot quietly go back to keeping its own copy.
    """
    clashes = sorted((n, ln) for n, ln in _module_level_assignments(driver_path).items()
                     if n in _OWNED)
    if clashes and strict:
        detail = ", ".join(f"{n} at line {ln}" for n, ln in clashes)
        raise RuntimeError(
            f"{pathlib.Path(driver_path).name} defines cell constants that belong to "
            f"ur15_cell_spec: {detail}. Read them from this module, or add the constant to the "
            f"p5 spec if it is genuinely new (spec §6.5).")
    return clashes


def self_check():
    """Check this module against its own sources.  Cheap, no simulation."""
    problems = []
    if CLIP_PARTS != _CLIP_PARTS_PER_SPEC:
        problems.append(
            f"the clip read from {_ENV_BASE.name} and turned a quarter turn is {CLIP_PARTS}, "
            f"but the clip design §3 states {_CLIP_PARTS_PER_SPEC}. One of the two moved.")
    seat = seat_z(0.0)
    if abs(seat - GROOVE_CENTER_Z) > 1e-12:
        problems.append(
            f"seat_z(0) is {seat} but task_config.GROOVE_CENTER_Z is {GROOVE_CENTER_Z}; the two "
            f"ways of expressing the same height disagree.")
    if abs(CABLE_N * CABLE_SEG - 0.600) > 1e-9:
        problems.append(
            f"{CABLE_N} links of {CABLE_SEG} m is {CABLE_N * CABLE_SEG:.3f} m, and "
            f"task_config.py:135 says the cable is 0.600 m.")
    return problems


if __name__ == "__main__":
    print(f"Tier A: TABLE_TOP={TABLE_TOP} CABLE_R={CABLE_R} CABLE_N={CABLE_N} "
          f"CABLE_SEG={CABLE_SEG} GRIP_HALF_SPAN={GRIP_HALF_SPAN}")
    print(f"        GROOVE_CENTER_Z={GROOVE_CENTER_Z} solref={CLIP_SOLREF} "
          f"friction={CLIP_FRICTION} collide={CLIP_COLLIDE}")
    print(f"        cable: {CABLE_N} x {CABLE_SEG * 1000:.0f} mm = {CABLE_N * CABLE_SEG:.3f} m, "
          f"radius {CABLE_R * 1000:.0f} mm")
    print("clip, turned a quarter turn from the env source:")
    for p in CLIP_PARTS:
        print(f"        pos=({p[0]:+.4f},{p[1]:+.4f},{p[2]:+.4f}) "
              f"half=({p[3]:.4f},{p[4]:.4f},{p[5]:.4f})")
    print(f"Tier B: YOKE_SPREAD={YOKE_SPREAD} TILT={math.degrees(math.pi/2 - TILT):.0f} deg "
          f"TABLE_HX/HY={TABLE_HX}/{TABLE_HY} REST_TOP={REST_TOP}")
    bad = self_check()
    print("self-check:", "all sources agree" if not bad else "\n  ".join(["PROBLEMS"] + bad))
    sys.exit(1 if bad else 0)
