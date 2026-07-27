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

Call `guard()` from a driver to fail loudly if that driver has redefined anything here.  guard()
checks NAMES only -- whether a driver has taken ownership of something that belongs here.  Whether
the values still agree with their sources is `self_check()`, a separate question; for the Tier A
figures it cannot fail, because they are imported rather than copied.
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
CABLE_N = _tc.CABLE_SEGMENTS                    # task_config.py:135 -- p5's final
                                                # ruling takes the SSOT cable whole,
                                                # so the count is imported again and
                                                # the derivation special case is gone
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

_ENV_BASE = pathlib.Path(_REPO, "thread_isaac_lab/envs/newton_skill_env_base.py")


def _clip_collides_in_source():
    """Does the env build its clips with collision on, unconditionally?

    Read rather than transcribed.  A written-down True says what someone believed when they typed
    it; this says what the source does now.  The env sets `shape_flags[idx] = 0x6` -- COLLIDE
    together with BROADPHASE -- with no flag or environment variable in front of it, which is the
    thing worth carrying over.  If that ever becomes conditional this returns False and the cell
    stops claiming otherwise.

    ⚠ An earlier version of this took the first two such assignments in walk order and happened to
    return the right answer for the wrong reason: walk order reaches the C2 spacer and line 1908
    but never 1925, and an unrelated edit flipped it.  p0 showed that with two counterfactuals.
    So take EVERY assignment on `scene.shape_flags` -- the arm pass writes to `proto.` and is not
    this question -- and require all of them.
    """
    tree = ast.parse(_ENV_BASE.read_text())
    flags = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
             for t in node.targets
             if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute)
             and t.value.attr == "shape_flags"
             and isinstance(t.value.value, ast.Name) and t.value.value.id == "scene"]
    return bool(flags) and all(isinstance(n.value, ast.Constant) and n.value.value == 0x6
                               for n in flags)


CLIP_COLLIDE = _clip_collides_in_source()   # clip design §6-A


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
REST_X = (-0.300, -0.055, +0.245)       # spec §4 -- placed by p5 inside the free windows this
                                        #            cell was measured to have; the previous
                                        #            three had one outside the shorter cable and
                                        #            one five millimetres into the right hand's
                                        #            zone.  These are saddle CENTRES.
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


def groove_width() -> float:
    """Clear width of the clip groove [m], off the two wall parts of the authoritative table."""
    walls = [q for q in CLIP_PARTS if abs(q[2] - 0.0125) < 1e-9]
    return 2.0 * (abs(walls[0][1]) - walls[0][4])


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


# The three sets the guard sorts a driver's module-level names into, per p5's contract.
#
# RETIRED are the names whose very existence is the bug: each was a cell constant that this
# directory kept two different values of, and the fix is not to agree on one but to stop having
# them.  Defining one at all fails, whatever value it is given.
RETIRED = {"CLIP_H", "GROOVE_W", "CLIP_RISER"}

# TIER-C is run-specific by design -- the spec §5 keeps these OUT so drivers can still differ.
TIER_C = {"OUT", "W", "H", "FPS", "HOLD_S", "WAY", "STEPS", "SEED",
          "CAM", "CAM2", "RENDERER", "FRAMES"}

_SPEC_MODULE = "ur15_cell_spec"


def _module_level_bindings(path):
    """Every name bound at module level in `path`, with how it was bound and what it was bound to.

    By syntax tree rather than by grep: grep misses tuple targets, and tuple targets are exactly
    how these drivers wrote the constants that disagreed (`GROOVE_W, CLIP_H = 0.016, 0.026`).

    Returns {name: (line, kind, node)} where kind is "assign", "sourced" (imported from the spec
    module), "import" (imported from anywhere else), or "star".
    """
    out = {}
    tree = ast.parse(pathlib.Path(path).read_text())
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.For, ast.AsyncFor)):
            targets = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            targets = [i.optional_vars for i in node.items if i.optional_vars]
        elif isinstance(node, ast.ImportFrom):
            src = (node.module or "").split(".")[-1]
            for a in node.names:
                if a.name == "*":
                    out["*"] = (node.lineno, "star", node)
                else:
                    kind = "sourced" if src == _SPEC_MODULE else "import"
                    out[a.asname or a.name] = (node.lineno, kind, node)
            continue
        elif isinstance(node, ast.Import):
            for a in node.names:
                out[(a.asname or a.name).split(".")[0]] = (node.lineno, "import", node)
            continue
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = (node.lineno, "assign", node)
            continue
        for t in targets:
            for leaf in ast.walk(t):
                if isinstance(leaf, ast.Name):
                    out[leaf.id] = (node.lineno, "assign", node)
    return out


def _has_bare_literal(node, known):
    """Does this value expression contain a number that does not come from a name we know about?

    p5's single rule for scope: a driver may bind whatever it likes as long as the value is
    derived from names that already have an owner.  The moment a bare number appears, the binding
    is carrying a constant of its own and has to say which set it belongs to.

    Small arithmetic factors are not exempted -- that was tempting, but "0.5 is obviously just
    arithmetic" is the same judgement call that let two files disagree about a cable radius.
    """
    value = getattr(node, "value", None)
    if value is None:
        return False
    for leaf in ast.walk(value):
        if isinstance(leaf, ast.Constant) and isinstance(leaf.value, (int, float)) \
                and not isinstance(leaf.value, bool):
            return True
        if isinstance(leaf, ast.Name) and leaf.id not in known:
            continue
    return False


def guard(driver_path, strict=True):
    """Sort a driver's module-level names into p5's contract, and fail on anything that breaks it.

    Fail-closed: a name that carries a number of its own and belongs to none of the three sets is
    a failure, not a pass.  Returns the list of (name, line, reason); with strict=True a non-empty
    list raises.
    """
    bindings = _module_level_bindings(driver_path)
    known = set(_OWNED) | RETIRED | TIER_C | set(bindings)
    bad = []
    for name, (line, kind, node) in sorted(bindings.items()):
        if name == "*":
            bad.append((name, line, f"`from {_SPEC_MODULE} import *` hides its own bindings from "
                                    f"the syntax tree, so nothing can check them"))
        elif name in RETIRED:
            bad.append((name, line, "retired: this constant is the divergence itself; the cell "
                                    "spec carries the clip geometry now, so it should not exist"))
        elif name in _OWNED and kind == "assign":
            bad.append((name, line, f"owned by {_SPEC_MODULE}; import it instead of redefining it"))
        elif name in _OWNED and kind == "import":
            bad.append((name, line, f"owned by {_SPEC_MODULE} but imported from somewhere else, "
                                    f"which is how a second copy starts"))
        elif kind == "assign" and name not in _OWNED and name not in TIER_C \
                and _has_bare_literal(node, known):
            bad.append((name, line, "carries a number of its own and belongs to none of the three "
                                    "sets: add it to the p5 spec, or derive it from names that "
                                    "are already owned"))
    if bad and strict:
        detail = "\n  ".join(f"{n} (line {ln}): {why}" for n, ln, why in bad)
        raise RuntimeError(f"{pathlib.Path(driver_path).name} does not satisfy the cell-constant "
                           f"contract:\n  {detail}")
    return bad


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
    # ⛔ `CABLE_N * CABLE_SEG == CABLE_TOTAL` is NOT a check -- CABLE_N is derived from those two,
    # so it holds by construction and would report nothing whatever went wrong.  p0 caught that.
    # The claim worth making lives at the source, where the SSOT binds the count and the step
    # INDEPENDENTLY and they can therefore still disagree with each other.
    ssot_total = _tc.CABLE_SEGMENTS * _tc.CABLE_SEG_LEN
    if abs(ssot_total - 0.600) > 1e-9:
        problems.append(
            f"task_config binds {_tc.CABLE_SEGMENTS} segments and a {_tc.CABLE_SEG_LEN} m step, "
            f"which is {ssot_total:.3f} m, but task_config.py:135 states 0.600 m. The SSOT's two "
            f"bindings have drifted apart.")
    # ⛔ `CABLE_N * CABLE_SEG == 0.600` is not a check on this module: both come from the same
    # SSOT, so the claim belongs where they are bound independently, which is the block above.
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
