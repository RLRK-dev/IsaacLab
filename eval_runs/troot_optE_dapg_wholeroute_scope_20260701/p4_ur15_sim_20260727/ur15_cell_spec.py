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
import os as _os_module
from os import environ as _os_env
import pathlib
import re
import sys
import xml.etree.ElementTree as _ET

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

# Distance from the pinch point to the claw tip [m].  The driver had this written out as a
# subtraction of two long decimals, which is the same value but stops being the same value the
# moment either end moves.
CLAW_OFFSET = _tc.EE_TO_PINCH_TIP_CLOSED - _tc.EE_TO_PINCH_CLOSED  # task_config.py:321 - :320


# --- the arm's own limits: read from the robot description, not transcribed --------------------
# The driver carried both as literal arrays, and the joint limits had been rounded on the way in
# (-6.283 for -6.283185307179586), which narrows the range the driver samples and unwraps within.

_URDF = pathlib.Path(__file__).with_name("ur15_mj.urdf")
ARM_JOINTS = ("shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
              "wrist_1_joint", "wrist_2_joint", "wrist_3_joint")


def _arm_limits_from_urdf():
    """(effort [N m], lower [rad], upper [rad]) per arm joint, in kinematic order."""
    root = _ET.parse(_URDF).getroot()
    joints = {j.get("name"): j for j in root.iter("joint")}
    out = []
    for name in ARM_JOINTS:
        j = joints.get(name)
        if j is None or j.find("limit") is None:
            raise RuntimeError(f"{_URDF.name} has no <limit> for {name}; the robot description "
                               f"moved, and this cell will not guess what it now says")
        lim = j.find("limit")
        out.append((float(lim.get("effort")), float(lim.get("lower")), float(lim.get("upper"))))
    return out


EFFORT = tuple(e for e, _, _ in _arm_limits_from_urdf())            # ur15_mj.urdf <limit effort>
LIMS = tuple((lo, hi) for _, lo, hi in _arm_limits_from_urdf())     # ur15_mj.urdf <limit lower/upper>


# --- how finely the producer integrates, and how finely this cell does ------------------------
# p5 spec §6.4j: the timestep is Tier A, and running coarser than the producer has to be a
# declared choice rather than something a template happened to say.  This cell was running 9.6x
# coarser, which p5 names as one candidate for today's cable-through-clip.

_PRODUCER = pathlib.Path(_REPO, "thread_isaac_lab/scripts/test_newton_clip_routing.py")


def _arithmetic(node):
    """Evaluate a numeric expression made only of literals and + - * /.

    The producer writes `DT = 1.0 / 480.0`, which `ast.literal_eval` refuses -- it is arithmetic,
    not a literal.  Copying the quotient across would defeat the point of reading the file, so
    this walks the two-operand expression instead.  Anything richer raises rather than guesses.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = _arithmetic(node.operand)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp):
        a, b = _arithmetic(node.left), _arithmetic(node.right)
        for op, fn in ((ast.Add, lambda: a + b), (ast.Sub, lambda: a - b),
                       (ast.Mult, lambda: a * b), (ast.Div, lambda: a / b)):
            if isinstance(node.op, op):
                return fn()
    raise RuntimeError(f"{ast.dump(node)[:60]} is not plain arithmetic; read it by hand")


def _producer_sim_dt() -> float:
    """The producer's solver step [s]: its own frame dt divided by the SSOT's substep count.

    ⚠ The two halves live in DIFFERENT files, and I had them in one.  `DT = 1.0 / 480.0` is the
    producer's (test_newton_clip_routing.py:123); `SIM_SUBSTEPS = 10` is task_config.py:101, which
    the producer IMPORTS (:111) and divides by at :124.  I cited both to the producer, which is
    the kind of citation that survives because the number it produces happens to be right.
    """
    tree = ast.parse(_PRODUCER.read_text())
    dt = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "DT":
            dt = _arithmetic(node.value)
    if dt is None:
        raise RuntimeError(f"{_PRODUCER.name} no longer defines DT at module level; this cell "
                           f"will not guess its step")
    return dt / _tc.SIM_SUBSTEPS


PRODUCER_SIM_DT = _producer_sim_dt()   # test_newton_clip_routing.py:123 / task_config.py:101

# The cell follows it.  Keeping the old coarse step would be allowed -- p5 §6.4j says a coarse
# run has to be an EXPLICIT choice -- but there was never a measurement behind 0.002, and the one
# thing known about it is that it is the deviation p5 lists as a candidate cause.  Deviating needs
# a reason; following the producer does not.
CELL_TIMESTEP = PRODUCER_SIM_DT

# The producer places NO limit on a cable bend joint (test_newton_clip_routing.py:1004-1017,
# add_joint_revolute with no limit_lower/limit_upper).  This cell wrote ±1.2 rad, which p5 ruled
# is a limit invented here: authority has none, so neither does the cell.  None means the template
# emits no range attribute at all, which is MuJoCo's unlimited.
CABLE_JOINT_RANGE = None


# --- cable physics: per-element quantities, DERIVED from the discretisation -------------------
# Halving the link length changes every one of these, and not all in the same direction.  The
# wiring landed the shorter link while the driver still wrote a literal mass and a literal joint
# stiffness, which made the cable 3.6x too heavy AND 64% too soft at the same time.  So each is
# derived here from the quantity that does not depend on how the cable is cut up.

CABLE_DENSITY = 1100.0          # task_config.py:138 verbatim "capsule volume x rho=1100"
# ⚠ NOT a pure constant at runtime.  test_newton_clip_routing.py:928 rescales this from the
# environment variable CABLE_BEND_STIFFNESS_OVERRIDE, so the value in task_config is what the
# producer starts from, not necessarily what it runs with.  Same shape as the collision flag: a
# name that reads like a fact and is actually a default.  self_check refuses to let this cell run
# while that override is set, rather than quietly disagreeing with the producer.
CABLE_BEND_EI = _tc.CABLE_BEND_STIFFNESS        # task_config.py:144 -- EI [N m^2], not a joint K
CABLE_BEND_DAMPING = _tc.CABLE_BEND_DAMPING     # task_config.py:152
CABLE_CONDIM = _tc.MUJOCO_CONTACT_CONDIM        # task_config.py:176
CABLE_FRICTION = tuple(_tc.MUJOCO_CABLE_TABLE_FRICTION)   # task_config.py:180


def cable_seg_mass() -> float:
    """Mass of one link [kg]: the capsule's own volume times the material density.

    A capsule is a cylinder plus a sphere's worth of end caps.  Leaving the caps out is a known
    error in this project's history -- task_config.py:140 records an old figure that did exactly
    that and came out 36% light.
    """
    r, L = CABLE_R, CABLE_SEG
    return (math.pi * r * r * L + (4.0 / 3.0) * math.pi * r ** 3) * CABLE_DENSITY


def bend_ei_in_force() -> tuple:
    """The EI actually in force, and where it came from.

    p5's disposition for the runtime override: do not forbid the second source, declare it.  An
    invisible second source becomes a visible one, which is the only version anyone can check.
    """
    raw = _os_env.get("CABLE_BEND_STIFFNESS_OVERRIDE", "")
    return (float(raw), "CABLE_BEND_STIFFNESS_OVERRIDE") if raw else (CABLE_BEND_EI,
                                                                      "task_config.py:144")


# The four packages whose versions decide what a measurement means.  p0's point, and it is a
# sharp one: my re-collation showed the output files were byte-identical, which proves the file
# did not change and says nothing about whether anything was re-run.  A copy would look the same.
# So every probe prints this, and then the output itself carries which substrate produced it.
STACK_PACKAGES = ("newton", "mujoco", "mujoco-warp", "warp-lang")


def stack_line() -> str:
    """One line naming the substrate this measurement was taken on."""
    from importlib import metadata
    out = []
    for name in STACK_PACKAGES:
        try:
            out.append(f"{name} {metadata.version(name)}")
        except metadata.PackageNotFoundError:
            out.append(f"{name} ABSENT")
    return " / ".join(out)


def announce():
    """Print the values whose source can move at runtime.  Call this at driver start-up."""
    ei, src = bend_ei_in_force()
    print(f"[cell] cable bend EI in force: {ei} N.m^2 from {src}"
          f"{'   <- NOT task_config; the producer rescales it' if 'OVERRIDE' in src else ''}")
    print(f"[cell] -> joint stiffness {ei / CABLE_SEG:.5f} N.m/rad over a {CABLE_SEG*1000:.0f} mm link")
    print(f"[cell] cable {CABLE_N} x {CABLE_SEG*1000:.0f} mm, {cable_seg_mass()*1000:.4f} g each, "
          f"{cable_seg_mass()*CABLE_N*1000:.2f} g total")
    print(f"[cell] clip collision read from the env source: {CLIP_COLLIDE}")


def cable_joint_k() -> float:
    """Bend stiffness of one joint [N m/rad] = EI / link length.

    task_config.py:146 verbatim: "CABLE_MUJOCO_BEND_K = EI/CABLE_SEG_LEN".  Shorter links means
    MORE joints over the same cable, so each one has to be stiffer, not softer -- the opposite
    direction to the mass.
    """
    return bend_ei_in_force()[0] / CABLE_SEG


_ENV_BASE = pathlib.Path(_REPO, "thread_isaac_lab/envs/newton_skill_env_base.py")


def _clip_collides_in_source(text=None):
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
    tree = ast.parse(_ENV_BASE.read_text() if text is None else text)
    parent = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node

    def creates_shape(node):
        """Does this subtree build the shape whose flags are being set?"""
        return any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                   and c.func.attr.startswith("add_shape") for c in ast.walk(node))

    def conditional(node):
        """Is the FLAG conditional, as opposed to the whole clip being conditional?

        Every one of these sites sits inside `if add_target_clip:` or its sibling, and those decide
        whether the clip exists at all -- not whether it collides once it does.  Reading those as
        conditionals says the env's clips might not collide, which is false and would be a loud
        wrong answer.  So walk up only as far as the construction that made the shape: an `if`
        between the two is a real guard on the flag; one above them both is a guard on the clip.
        This is p5's "roll up one line" for the false positives.
        """
        if isinstance(node.value, ast.IfExp):
            return True
        cur, child = parent.get(node), node
        while cur is not None:
            if creates_shape(cur):
                return False
            if isinstance(cur, ast.If) and child in (cur.body + cur.orelse):
                return True
            cur, child = parent.get(cur), cur
        return False

    flags = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
             for t in n.targets
             if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute)
             and t.value.attr == "shape_flags"
             and isinstance(t.value.value, ast.Name) and t.value.value.id == "scene"]
    return bool(flags) and all(isinstance(n.value, ast.Constant) and n.value.value == 0x6
                               and not conditional(n) for n in flags)


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
TABLE_HZ = 0.02                         # spec §6.4j -- table top half-thickness, new here

# The scenery, placed by spec §6.4j.  None of these is new: each was a literal in the driver's XML
# where no name check could see it, and they are moved with what the driver knew about them.
FLOOR_HALF = 6.0                        # spec §6.4j -- ground plane half extent; the plane is
FLOOR_SPACING = 0.1                     #               non-colliding, so this is what you see,
                                        #               but `size` is geometry and stays checked
COLUMN_R = 0.102                        # spec §6.4j -- the shared column both arms stand on
COLUMN_HZ = SHOULDER_HEIGHT / 2         # half-height, because MuJoCo cylinders take one.
                                        # The halving lives here: under the strict form a
                                        # driver cannot write /2, and this is where the
                                        # derivations are supposed to be anyway.
PEDESTAL_R, PEDESTAL_HZ = 0.215, 0.03   # spec §6.4j -- its foot

REST_POST_HALF = 0.014                  # spec §6.4j -- saddle post, square in plan
REST_LIP_HY, REST_LIP_HZ = 0.004, 0.006  # spec §6.4j -- the two lips that capture the cable
REST_LIP_DY = 0.012                     # spec §6.4j -- how far each lip sits off centre

REST_TOP = TABLE_TOP + 0.150            # spec §4 -- "at +0.060 the open fingers press into the
                                        #            table".  ⚠ p4's own gripper-only measurement
                                        #            (36 mm of reach below the cable with the
                                        #            fingers open) does not reproduce that, so the
                                        #            note may have been seeing the wrist above the
                                        #            gripper.  Unresolved; see
                                        #            P4_FINGER_REACH_BELOW_CABLE_20260727.md §4.

# --- dimensionless conventions: cell facts that no literal check would ever have caught ---------
# Spec §6.4f, p5's second class: the guard excuses these (unit quaternions and index integers) and
# they are still facts about this cell -- which side is which, and how the tool is meant to hang.
# A rule cannot find them, so the spec owns them by decision instead.

SIDES = {"L": -1.0, "R": +1.0}           # spec §6.4f -- the sign convention, left negative in y

# Desired tool orientation: closing axis along world y, across the cable; approach along world z,
# so the gripper hangs down with the pinch at the bottom.  Rows, in the tool's own frame.
R_DES = ((0.0, -1.0, 0.0),
         (1.0, 0.0, 0.0),
         (0.0, 0.0, 1.0))                # spec §6.4f -- the reference attitude

# --- the thirteen names spec §6.4j says to move here, less one ---------------------------------
# p5: "already OWNED in §6.4d, so just move them into the spec module".  Each keeps what the
# driver knew about it, because that provenance is the only thing that makes them not-invented.

CLIP_Y_ODD, CLIP_Y_EVEN = 0.35, 0.40    # spec §6.4d -- the two clip rows
C1 = (0.150, CLIP_Y_ODD)                # spec §6.4d -- first clip, on the near row
C2 = (0.040, CLIP_Y_EVEN)               # spec §6.4d -- second clip, on the far row

Z_HOME = TABLE_TOP + 0.20               # spec §6.4d -- where the arms wait
Z_RISE_ROUTE = TABLE_TOP + 0.180        # spec §6.4d -- carry height between clips
Z_RISE_REST = TABLE_TOP + 0.230         # spec §6.4d -- clearance over the saddle row

# Choreography timings.  ⚠ These are DURATIONS, and the driver used to hold three of them as step
# counts, which stopped meaning the same thing the moment the timestep moved: 4000 steps was 8 s
# at the old 0.002 and is 0.83 s at the producer's.  Seconds survive a change of substrate; step
# counts silently do not.
# The claw-tip gap at which a cable can leave the jaw [m].  Clip design §12-5 gives 8.00 mm and
# §12-6 requires that release be judged on THIS and not on grasped(), which errs both ways: it
# says held when the claws have closed through each other, and released when the cable is still
# surrounded.  8.00 mm is the cable's own diameter, so it is derived here rather than written --
# a thinner SSOT cable moves the floor with it.  ⚠ If p5 measured 8.00 as something other than
# the diameter and the two merely agree today, this should become a carried number instead.
CLAW_RELEASE_GAP = 2.0 * CABLE_R        # clip design §12-5 / §12-6

# The mouth band, pad-local z [m]: the cable's centre has to be inside the jaw's mouth, not merely
# between the claw tips.  Clip design §13 (p5 -099), the weak form of the conjunction.
#
# Derived, not written.  It was a pair of literals and it went stale the moment Rs moved a claw --
# twice over, because the value supplied to replace it was read before the same move.  p5's rule:
# the band runs between the two plates' INNER faces, and min/max rather than first/second so it
# survives the two being listed in either order.  The far faces were rejected: they would count a
# cable centred inside the thickness of a plate as inside the mouth.
GRIP_XML_PATH = pathlib.Path(
    _REPO, "thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml")


def mouth_band_z(model=None):
    """(lo, hi) pad-local z of the mouth interior [m], read from the asset."""
    import xml.etree.ElementTree as _E
    root = _E.parse(GRIP_XML_PATH).getroot()
    zs, half = [], None
    for g in root.iter("geom"):
        n = g.get("name") or ""
        if n.endswith(("_pad_f1ext", "_pad_f2ext")) and n.startswith("left"):
            zs.append(float(g.get("pos").split()[2]))
            half = float(g.get("size").split()[2])
    if len(zs) != 2 or half is None:
        raise RuntimeError(f"{GRIP_XML_PATH} no longer has exactly two left-pad claw plates; the "
                           f"mouth band cannot be derived and will not be guessed")
    return min(zs) + half, max(zs) - half


MOUTH_BAND_Z = mouth_band_z()           # clip design §13-3 R6(ii) -- derived above

# The claw-tip reading saturates once the two tips overlap, so a claw gap cannot be read directly
# near closure.  p5's route: measure at the BACKPLATE, which does not saturate, and convert with
# the offset between the two -- which is not a constant but a function of the opening (9.99 mm at
# full open to 10.21 closed, clip design §12-12).  That function is read from the banked sweep.
_SWEEP = pathlib.Path(__file__).with_name("sweep_raw_23points.txt")


def _sweep_rows():
    """(pad gap, claw gap) in mm from the banked sweep, saturated rows dropped.

    Saturation is excluded by SIGN, not by a floor: `mj_geomDistance` returns a real separation
    while the tips are apart and a clamped value once they overlap, so a negative reading is the
    query's floor rather than a distance.  Keeping only positive rows needs no measured constant --
    naming a floor would put p0's withdrawn 2.40 back into the code.

    ⚠ My first version detected saturation as "the reading stopped falling", and it kept the
    saturated rows: those readings DO keep drifting down (-2.55, -2.59, -2.64, -2.75), so nothing
    tripped.  The offset it produced ran from 1.62 to 10.22 mm instead of 9.99 to 10.21, which is
    how it was caught.
    """
    rows = []
    for line in _SWEEP.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 3:
            try:
                rows.append((int(parts[0]), float(parts[1]), float(parts[2])))
            except ValueError:
                continue
    rows.sort()
    return [(pad, claw) for _ctrl, pad, claw in rows if claw > 0.0]


def offset_at(pad_gap_mm: float) -> float:
    """Backplate-to-claw-tip offset [mm] at this opening, READ from the measured sweep.

    p5 -100: do NOT derive this the way the 8.00 is derived.  The geometric 10.00 is not the
    offset -- the claws swing as the jaw closes, so it runs 9.99 to 10.21 across the range, and a
    floor built on 10.00 comes out short.  The diameter has a single source (CABLE_R, Tier A); the
    offset has a different one (the sweep table).  Two origins, and the floor needs both.
    """
    return pad_gap_mm - claw_from_backplate(pad_gap_mm)


def release_floor(seed_offset_mm: float = 10.20) -> float:
    """The BACKPLATE gap at which a cable can leave [mm].

    p11 -094: the definition is IMPLICIT -- the floor is the gap where the tips are exactly one
    cable-diameter apart, and the offset has to be evaluated AT that gap, not at wherever the jaw
    happens to be:

        floor = 2 x CABLE_R + offset(floor)

    Written the explicit way it looks like it needs a gap you do not have yet.  It converges at
    once because the offset only moves 0.22 mm across the whole range: seeded at 2r + 10.20 it
    goes 18.20 -> 18.19 -> 18.19.  The seed does not decide the answer; the fixed point does.
    """
    floor = 2.0 * CABLE_R * 1000.0 + seed_offset_mm
    for _ in range(3):
        floor = 2.0 * CABLE_R * 1000.0 + offset_at(floor)
    return floor


def claw_from_backplate(pad_gap_mm: float) -> float:
    """Claw-tip gap [mm] inferred from the backplate gap, via the measured offset."""
    rows = sorted(_sweep_rows())
    pads = [p for p, _ in rows]
    offs = [p - c for p, c in rows]
    if pad_gap_mm <= pads[0]:
        return pad_gap_mm - offs[0]
    if pad_gap_mm >= pads[-1]:
        return pad_gap_mm - offs[-1]
    for i in range(1, len(pads)):
        if pad_gap_mm <= pads[i]:
            f = (pad_gap_mm - pads[i - 1]) / (pads[i] - pads[i - 1])
            return pad_gap_mm - (offs[i - 1] + f * (offs[i] - offs[i - 1]))
    return pad_gap_mm - offs[-1]

SETTLE_S = 5.0                          # spec §6.4d -- was `range(2500)` at dt 0.002

# How long a scratch PREDICTION settles.  Not the same question as SETTLE_S: that is what the run
# waits before it lets the fingers move, and it stays.  This is how long the attitude search has to
# simulate to find out where a jaw would land -- and measured (probe_prediction_settle.py) the
# answer stops moving at 1.5 s: identical to the 5 s answer to four decimal places, with 1.0 s
# already within a tenth of a micron.  The search runs this 130 times, so settling for 5 s was
# costing eleven minutes an iteration and buying nothing.
PREDICT_S = 1.5                         # measured, not chosen
START_RAMP_S = 8.0                      # spec §6.4d -- was `RAMP = 4000`
START_HOLD_S = 6.0                      # spec §6.4d -- was the `+ 3000` after it

FINGER_RAMP = 0.75                      # spec §6.4d -- "stepping the command shut the jaw in
                                        #   0.544 s (149.2 mm/s); ramping over 0.75 s gives
                                        #   1.084 s (74.9 mm/s) -- half the speed, measured"
SETTLE_TOL = 0.002                      # spec §6.4d -- rad; the arm must be this close to its
                                        #   command before the jaw is allowed to move

# How far off straight down a descending jaw may be before the run stops.  Rs, 2026-07-28:
# descending to a clip, all the fingers have to point vertically down, so they do not hit the
# table.
#
# ⛔ MY FIRST RATIONALE WAS WRONG TWICE and both are recorded because the second is the one that
# matters.  I wrote "half of 0.2 rad, the smallest non-zero roll the attitude menu offers": the
# menu's smallest non-zero roll is 0.10 (GRASP_ATTITUDES below), so the number was wrong -- and
# the KIND was wrong, which p5 and p11 caught independently.  Menu spacing is a property of the
# menu.  The requirement is about the table.  Tying a limit to how finely someone happened to
# sample attitudes is the same error as putting a bar on a quantity that has no units.
#
# The right form, from p11: the allowance is whatever keeps the arm's lowest point above the table
# at seat height -- a tilt the cell itself decides, measured at 10.5 to 14.6 degrees depending on
# where the lowest point is taken.  ⚠ The VALUE below is NOT ratified: p5 rejects 5.73 as letting
# the adjacent case through, p11 accepts it for today and targets 2.86.  Both accept 2.86.  It is
# left where it is until the two agree on the basis, and the run now prints the angle it actually
# achieves so the decision is made on a measurement instead of on a preference.
VERTICAL_TOL_DEG = 5.73
# Pose selection and the singularity.  The floor below was set to 0.0 with a recorded reason --
# "the 0.12 floor starved the solver ... ranking, not rejection, is the way to do this" -- and the
# ranking was never written: the selector computes each candidate's smallest singular value, PRINTS
# it, and then orders candidates by roll and joint travel only.  So a pose that has lost a
# direction can win, and did: Rs saw the arm swing through a singularity two runs running, and the
# grasp step runs at 0.0381, a third of the floor that used to apply.
#
# These two put it into the ranking instead of back into a filter, so a well-conditioned pose is
# preferred without any pose being forbidden.
SIGMA_GOOD = 0.12                       # spec: the withdrawn floor, reused as the value to aim
                                        #   for.  VALUE = the measuring lane, as SIGMA_FLOOR
SIGMA_PENALTY = 3.0                     # spec: the weight on falling short of it.  VALUE = the
                                        #   measuring lane -- ⚠ this one is MINE and unmeasured,
                                        #   set so half of SIGMA_GOOD costs about a 1.5 rad joint
                                        #   move.  p11 -106 has ruled the weight is not the fix
                                        #   and must not be tuned; the path-sigma bar replaces it
                                        #   and comes from measurement.

SIGMA_FLOOR = 0.0                       # spec §6.4d -- "the 0.12 floor starved the solver: it
                                        #   picked poses the servos could not hold, so the arms
                                        #   never settled and the jaw stayed 80 mm open.  Ranking,
                                        #   not rejection, is the way to do this."

# Grasp attitude candidates: yaw x roll, coarse near upright and finer where the claws engage.
TABLE_Y = (REST_Y + CLIP_Y_EVEN) / 2    # the table is centred between the saddle row
                                        # and the far clip row.  Defined after both,
                                        # since a spec module is read top to bottom.

GRASP_ATTITUDES = [(y, r) for r in (0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.55, 0.60, 0.65,
                                    0.70, 0.75, 0.85, 0.95)
                   for y in (0.0, 0.15, -0.15, 0.30, -0.30)]     # spec §6.4d

# The thirteenth.  p5 settled the conflict between their own two rulings by keeping §6.4j and
# withdrawing the refusal, and the reason is worth carrying: withholding a value does not leave
# the cell without one -- it makes the driver invent one, which is the second source this whole
# module exists to prevent.  So the single source holds a provisional value and says so here.
#
# ⛔ NOT a settled figure.  It is the fail-closed start: the clip sits on the table.  The ONLY
# reason to raise it is arm reach (clip design §10-4); nothing else is grounds for moving it.
FLOAT_Z = 0.0                           # spec §6.4l

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
def float_z() -> float:
    """How high the whole clip stands off the table [m].

    This used to raise.  p5 withdrew that: refusing to supply a value does not leave the cell
    without one, it makes the driver write its own, and a second source is the failure this
    module exists to prevent.  Provisional is a NOTE, not an absence -- see FLOAT_Z.
    """
    return FLOAT_Z


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
# The lower-case entries are p5's own placements in spec §6.4d: `frames` `log` `n` are recording
# bookkeeping and `claw_min` `col_min` `sig_min` are running minima whose 1e9 is a sentinel rather
# than an input.
TIER_C = {"OUT", "W", "H", "FPS", "HOLD_S", "WAY", "STEPS", "SEED",
          "CAM", "CAM2", "RENDERER", "FRAMES",
          "frames", "log", "n", "claw_min", "col_min", "sig_min",
          # p5 §6.4j: these are in spec §6.4d as DERIVED and are free.  I had reported them as
          # absent from §6.4d, which was a bad read of my own -- they are on its line 195, in the
          # DERIVED row rather than the TIER-C row I was looking at.
          # cam3 is the top-down view Rs asked for on 2026-07-28.  Same tier and same reason as
          # the other two: it says how a run is recorded and never reaches the model.
          "cam", "cam2", "cam3", "render_every",
          # The watch-along file Rs asked for on 2026-07-28, and the one encoder setting its
          # writer shares with the finished one.  Tier C by the same reading as OUT/W/H/FPS: they
          # say how a run is recorded, and carry no cell geometry -- nothing here can disagree
          # with the asset, because none of it reaches the model.  Taking the path the guard's own
          # message offers ("add it to the p5 spec"); flagged to p5 for ratification rather than
          # assumed, since the tier classification is p5's to make.
          "LIVE_OUT", "_live", "VIDEO_QUALITY"}

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


# ⛔ There is no set of excused coefficients.  p5's final ruling (spec §6.4h as landed): the fix
# for a set with holes in it is not a better set -- it is no set.  Two versions of this module
# carried one (mine by size and spelling, then the combined form with p0), and each time the
# boundary members moved: `2` free but `2.0` caught, `1000.0` free but `1.0375` caught.  A rule
# whose answer depends on how a number is spelled is a rule that will be wrong quietly.
#
# So a literal in a multiplication or division is classified like any other.  What survives is
# only what counts rather than measures: bare 0 and 1, and integers used as indices, in range(),
# or in comparisons.


def _counting_position(node, parent):
    """Is this integer counting rather than measuring -- an index, a range, a comparison?

    Spec §6.4d exempts these three, and only for integers: `q[2]` and `range(3)` are structural,
    while `q[0.02]` is not a thing anyone writes.
    """
    cur, child = parent.get(node), node
    while cur is not None:
        if isinstance(cur, ast.Subscript) and child is cur.slice:
            return True
        if isinstance(cur, ast.Compare):
            return True
        if isinstance(cur, ast.Call) and isinstance(cur.func, ast.Name) and cur.func.id == "range":
            return True
        cur, child = parent.get(cur), cur
    return False


def _unowned_literals(node):
    """Numbers written into this binding that the contract does not excuse.

    The earlier version failed on any numeric literal at all, which was p5's strict reading after
    my first docstring promised an exemption the code never implemented.  The strictness stays;
    what changes is that the two exemptions p5 has since ruled on are now IMPLEMENTED rather than
    described -- and they are implemented as one rule about position, not a list of names:

      * added or subtracted -> the literal has the same unit as what it is added to, so it is a
        cell constant.  `TABLE_TOP + 0.2` is a height and gets caught.
      * multiplied or divided -> also classified.  p5's final ruling removed the excused-factor
        set rather than repairing it; a driver that wants a half writes it as a name.
      * bare 0 and 1 anywhere, and integers used as an index, in `range()`, or in a comparison
        -> counting, not measuring.
    """
    value = getattr(node, "value", None)
    if value is None:
        return []
    parent = {}
    for p in ast.walk(value):
        for c in ast.iter_child_nodes(p):
            parent[c] = p
    out = []
    for leaf in ast.walk(value):
        if not (isinstance(leaf, ast.Constant) and isinstance(leaf.value, (int, float))
                and not isinstance(leaf.value, bool)):
            continue
        # fold a leading minus into the literal, per p5's acceptance of p0 `-316`(2): otherwise
        # REST_X's -0.300 is a UnaryOp wrapping a bare 0.300 and reads as unowned twice over.
        here = leaf
        up = parent.get(here)
        if isinstance(up, ast.UnaryOp) and isinstance(up.op, (ast.USub, ast.UAdd)):
            here, up = up, parent.get(up)
        # p5 §6.4j, one step wider than the three counting positions: a bare integer 0 or 1 is
        # exempt wherever it stands.  It closes the false positive on `sum(1 for ...)` and it is
        # safe for the reason p5 gives -- no cell dimension is exactly 0 or 1, while an integer
        # cell quantity like CABLE_N = 40 is neither, so it still gets caught.
        if isinstance(leaf.value, int) and leaf.value in (0, 1):
            continue
        if isinstance(leaf.value, int) and _counting_position(here, parent):
            continue
        out.append(leaf.value)
    return out


# --------------------------------------------------------------------------------------------
# The template rule -- spec §6.4e.  The name checks above cannot see inside a string, and the XML
# the driver builds is a string, so the cell's geometry was living in the one place nothing looked.
# p5 withdrew the first version (a list of four geometry attributes: it covered 27 of 59 sites and
# missed ten burnt-in physics values) and inverted it instead: EVERY number in the static text of
# a template fails, with two exceptions.  Inverting it means tomorrow's sixtieth attribute is
# caught without anyone adding it to a list.
# --------------------------------------------------------------------------------------------

# Exception 1 -- attributes that only change how the cell LOOKS.  Nothing here reaches the solver.
DRAWING_ATTRS = frozenset({
    "rgba", "material", "texture", "texrepeat", "reflectance", "rgb1", "rgb2", "markrgb",
    "ambient", "diffuse", "specular", "shininess", "emission",
    "width", "height", "offwidth", "offheight", "znear", "zfar", "shadowsize", "fovy",
})

# Exception 2 -- `0` and `1` themselves: origins, axis directions, unit quaternions, and the
# contact flags.  Spelling is the discriminator and it is deliberate: a friction of "1" would slip
# through here, but a friction of "1.0" is caught, and nobody writes an origin as "0.0 0.0 0.0".
_BARE_UNITS = frozenset({"0", "1", "-1", "+1"})

_ATTR_IN_TEMPLATE = re.compile(r'([A-Za-z_][\w:.-]*)\s*=\s*"([^"]*)"')
_NUMBER_IN_VALUE = re.compile(r'(?<![\w.])[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?(?![\w.])')
_SUBSTITUTION = "\x00"


def _templates(tree):
    """Every string the module builds, with each `{...}` substitution replaced by one marker.

    Reconstructing the f-string rather than reading its pieces is what lets an attribute be read
    when it is PART static and PART substituted -- `size="0.102 {SHOULDER_HEIGHT/2:.4f}"` splits
    into three AST nodes, and looking at them separately loses both the attribute name and the
    fact that 0.102 is one of its numbers.
    """
    inner = {id(v) for n in ast.walk(tree) if isinstance(n, ast.JoinedStr) for v in n.values}
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            yield node.lineno, "".join(
                v.value if isinstance(v, ast.Constant) and isinstance(v.value, str)
                else _SUBSTITUTION for v in node.values)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in inner:
            yield node.lineno, node.value


def template_literals(driver_path):
    """Numbers written into the static text of the driver's XML.  Spec §6.4e.

    Returns [(line, attribute, whole value, the literal)].  Only attribute values are examined:
    a number in prose inside a comment is not a cell constant, and the geometry is all in
    attributes.
    """
    tree = ast.parse(pathlib.Path(driver_path).read_text())
    out = []
    for lineno, text in _templates(tree):
        if '="' not in text:
            continue
        for m in _ATTR_IN_TEMPLATE.finditer(text):
            attr, value = m.group(1), m.group(2)
            if attr in DRAWING_ATTRS:
                continue
            for num in _NUMBER_IN_VALUE.finditer(value):
                if num.group(0) not in _BARE_UNITS:
                    out.append((lineno, attr, value.replace(_SUBSTITUTION, "{}"), num.group(0)))
    return out


def guard(driver_path, strict=True):
    """Sort a driver's module-level names into p5's contract, and fail on anything that breaks it.

    Fail-closed: a name that carries a number of its own and belongs to none of the three sets is
    a failure, not a pass.  Returns the list of (name, line, reason); with strict=True a non-empty
    list raises.
    """
    bindings = _module_level_bindings(driver_path)
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
                and _unowned_literals(node):
            bad.append((name, line, "carries a number of its own and belongs to none of the three "
                                    "sets: add it to the p5 spec, or derive it from names that "
                                    "are already owned"))
    # Retired names get checked for USE as well as for definition.  Checking only definitions is
    # a check that cannot fail in the direction that matters: I removed CLIP_RISER's definition,
    # verified nothing defined it, and left three places still reading it -- which is a NameError
    # the moment that line runs, and the first run found it in its first minute of choreography.
    used = {n.id: n.lineno for n in ast.walk(ast.parse(pathlib.Path(driver_path).read_text()))
            if isinstance(n, ast.Name) and n.id in RETIRED}
    for name, line in sorted(used.items()):
        bad.append((name, line, "retired, and still READ here: the cell spec carries the clip "
                                "geometry now, so this raises NameError when the line runs"))
    for line, attr, value, literal in template_literals(driver_path):
        bad.append((f'{attr}="{value}"', line,
                    f"{literal} is written into the XML this driver builds.  The templates are "
                    f"where the cell's geometry actually lives, and no name check can see inside "
                    f"a string, so a number here is outside every other rule in this module.  "
                    f"Substitute it from an owned name"))
    if bad and strict:
        detail = "\n  ".join(f"{n} (line {ln}): {why}" for n, ln, why in bad)
        raise RuntimeError(f"{pathlib.Path(driver_path).name} does not satisfy the cell-constant "
                           f"contract:\n  {detail}")
    return bad


def cross_check_measurable(measured: dict, tol_mm: float = 1.0):
    """Every Tier A value the running cell can measure for itself, checked against it.

    ⛔ This exists because of a failure of mine on 2026-07-27.  CLAW_OFFSET had been measured that
    day as -44.4 / -39.8 mm and found wrong at +20.9; hours later I put +20.9 back into this module
    because task_config carries it -- reasoning that a value with an authoritative source belongs
    in Tier A.  Having a source and being right are different properties, and nothing here was
    checking the second one.

    So: pass in what the cell measures, keyed by the name it corresponds to, and a disagreement
    raises.  A note in a log does not stop anything; this does.
    """
    owned = {"CLAW_OFFSET": CLAW_OFFSET}
    bad = []
    for name, meas_m in measured.items():
        if name not in owned:
            continue
        diff_mm = abs(owned[name] - meas_m) * 1000.0
        if diff_mm > tol_mm:
            bad.append(f"{name}: this module carries {owned[name]*1000:+.2f} mm, the cell measures "
                       f"{meas_m*1000:+.2f} mm -- {diff_mm:.2f} mm apart")
    if bad:
        raise RuntimeError("a Tier A value disagrees with what the cell measures:\n  "
                           + "\n  ".join(bad))
    return sorted(measured)


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
    override = _os_env.get("CABLE_BEND_STIFFNESS_OVERRIDE")
    if override:
        problems.append(
            f"CABLE_BEND_STIFFNESS_OVERRIDE is set to {override!r}, which the producer applies at "
            f"runtime (test_newton_clip_routing.py:928). This cell derives its joint stiffness "
            f"from task_config's {CABLE_BEND_EI} and would silently disagree with it.")
    seg_g = cable_seg_mass() * 1000.0
    if abs(seg_g - 1.1243) > 5e-4 and abs(CABLE_SEG - 0.015) < 1e-12:
        problems.append(
            f"one link works out at {seg_g:.4f} g, but task_config.py:138 states 1.1243 g/seg "
            f"for this 15 mm link -- the density or the capsule formula is wrong.")
    total = cable_seg_mass() * CABLE_N
    if abs(total - 0.04497085511684418) > 1e-5 and abs(CABLE_SEG - 0.015) < 1e-12:
        problems.append(
            f"the whole cable works out at {total*1000:.2f} g against the measured "
            f"44.97 g at task_config.py:139.")
    return problems



# Speak on IMPORT, not only when run as a script.  The thing worth leaving a trace of is a run
# that used the override, and a run imports this module rather than executing it -- p0 measured
# that the declaration was silent exactly in the case it exists for.
if _os_env.get("CABLE_BEND_STIFFNESS_OVERRIDE"):
    print(f"[cell] ⚠ CABLE_BEND_STIFFNESS_OVERRIDE = "
          f"{_os_env['CABLE_BEND_STIFFNESS_OVERRIDE']!r} is in force: the cable's bend EI does "
          f"NOT come from task_config.py:144, and this cell's joint stiffness follows the "
          f"override. self_check() will refuse while it is set.")


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
