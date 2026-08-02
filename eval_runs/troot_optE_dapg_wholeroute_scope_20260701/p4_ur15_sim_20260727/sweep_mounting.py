"""Two mounting sweeps: the crown's radius, and spread x tilt -- p5 -176(4).

(a) CROWN RADIUS, with "no crown at all" as the lower bound.  p5's own disclosure is why this
    point matters: the crown's size came from a photograph and the reference asset carries no
    crown collision shape, so the most weakly grounded number in the mounting is also the one the
    y sweep found dominant.  Removing it says how much of the blockage it actually owns.

(b) SPREAD x TILT, wired to TWO readouts, because it is the same sweep as a question that has
    been open since the spec comment was written: the pair (0.22, 45) was measured once to make
    the two arms interleave at an 88 mm span, and (0.40, 20) not to.  So each point reports the
    clear-candidate count AND the closest distance between the two arms at the commanded span.
    ⚠ The pair is not separated: both numbers are read at every combination, so a claim about one
    cannot be lifted off a point that was only measured for the other.

⛔ Neither table decides anything.  Both are the numbers p5 asked for.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = "/home/rlrk/env_isaaclab7/bin/python"
CNT = re.compile(r"start-pose IK ([LR]): (\d+) solved / (\d+) collision-free")
WHY = re.compile(r"start-pose IK ([LR]): rejected against -- (.*?)\s{3}\(parts named")
ILV = re.compile(r"88mm-SPAN INTERLEAVE: arms closest ([-+\d.]+) mm \(([^)]*)\)|"
                 r"88mm-SPAN INTERLEAVE: arms closest (nothing within[^ ]* \d+ mm[^ ]* radius)")
# 260 was tuned for 24 draws.  At 240 the two solves take about four and a half minutes and the
# cut fell BETWEEN them: the first six points of the 240 grid came back with left counts and
# R = None, gap = "?" -- rows that look like measurements and are truncations.  The wait breaks
# as soon as the interleave line appears, so a generous cap costs nothing on a fast point and is
# the only thing between a slow point and a silently half-filled table.
# ⛔ WITHDRAWN, and left here as the correction: I raised this to 2400 believing a point had run
# past fifteen minutes, and wrote a physical reason for it (wider spread -> more geom pairs inside
# the cutoff -> costlier candidates).  Neither was measured.  The point had SEGFAULTED in 37 s,
# and the "fifteen minutes" came from the error text, which interpolated this constant instead of
# the elapsed time.  The cap has never fired.  It stays as insurance against a genuinely slow
# point, and it is not evidence about any point.  See SEGFAULT_AT_SPREAD0340_TILT30_20260802.md.
TIMEOUT_S = int(os.environ.get("SWEEP_TIMEOUT_S", "2400"))
# The draw count is part of the table's identity, not a detail of how it was run: a 24-draw grid
# and a 240-draw grid have the same shape and different numbers.  It goes in the file name.
TRIES = os.environ.get("START_TRIES", "24")


def measured_on(L, R):
    """What the interleave reading on this row was measured on.

    ⭐ The gap is read with both arms at their CHOSEN poses, and when an arm has no clear
    candidate the driver puts them all back and chooses among rejected ones.  The printed
    collision-free count IS len(_strict), so a zero there is the fallback -- the fact was always
    in the table, with nothing saying it governed the two columns beside it.
    ⚠ It changes no verdict (a zero fails the conjunction on its first leg); it decides whether
    the interleave may be read on its own, which is the spec comment's question.
    """
    lf, rf = (L[1] or 0), (R[1] or 0)
    if lf and rf:
        return "both clear"
    return "BOTH put back" if not lf and not rf else ("L put back" if not lf else "R put back")


def _truncated(L, R, gap):
    """The point did not finish -- a count is missing, or the interleave line never appeared."""
    return L[0] is None or R[0] is None or gap == "?"


def _separated(L, R, gap):
    """Are the arms apart at the chosen poses?

    ⛔ "beyond radius" IS a reading -- nothing within the search radius means nothing close.
    "?" is NOT: it is a point that was cut off.  These two used to share one except-branch, so a
    truncated point could be printed as PASS.
    """
    if _truncated(L, R, gap):
        return False
    return True if gap == "beyond radius" else float(gap) > 0


def one(env_extra: dict, log: Path, reuse_after: float = 0.0):
    # ⭐ Resume.  A point whose log is newer than `reuse_after` AND already carries the interleave
    # line was measured by THIS run and is parsed instead of re-solved.  ⛔ The floor is required
    # and explicit: /tmp holds the previous grid's logs under the same names, so an unguarded
    # reuse would read a 24-draw point into a 240-draw table.
    if reuse_after and log.exists() and log.stat().st_mtime >= reuse_after:
        _t = log.read_text(errors="replace")
        if "88mm-SPAN INTERLEAVE" in _t:
            mm = ILV.search(_t)
            return ({m[0]: (int(m[1]), int(m[2])) for m in CNT.findall(_t)},
                    {m[0]: m[1] for m in WHY.findall(_t)},
                    mm.group(1) if mm and mm.group(1) else "beyond radius",
                    (mm.group(2) if mm and mm.group(2) else "") + " [reused]", "reused")
    env = dict(os.environ, **{k: str(v) for k, v in env_extra.items()})
    with log.open("wb") as fh:
        p = subprocess.Popen([PY, "-u", "ur15_steps_wired.py"], cwd=HERE, env=env,
                             stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        t0 = time.time()
        while time.time() - t0 < TIMEOUT_S and p.poll() is None:
            if "88mm-SPAN INTERLEAVE" in log.read_text(errors="replace"):
                break
            time.sleep(2.0)
        # ⛔ How the wait ended, measured, not inferred from what is missing.  The row used to say
        # "no interleave line within {TIMEOUT_S}s" whichever way a point failed -- and the one
        # point that ever failed had segfaulted in 37 s, so the row named a cap that was never
        # reached.  A caller cannot tell "no line yet" from "no line ever"; only this can.
        _rc, _el = p.poll(), time.time() - t0
        if _rc is None:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            p.wait(timeout=30)
            how = f"cap {TIMEOUT_S}s reached at {_el:.0f}s"
        elif _rc < 0:
            how = f"killed by signal {-_rc} after {_el:.1f}s"
        elif _rc > 0:
            how = f"exited {_rc} after {_el:.1f}s"
        else:
            how = f"finished in {_el:.1f}s"
    txt = log.read_text(errors="replace")
    cnt = {m[0]: (int(m[1]), int(m[2])) for m in CNT.findall(txt)}
    why = {m[0]: m[1] for m in WHY.findall(txt)}
    mm = ILV.search(txt)
    gap = mm.group(1) if mm and mm.group(1) else ("beyond radius" if mm else "?")
    who = mm.group(2) if mm and mm.group(2) else ""
    return cnt, why, gap, who, how


def main() -> int:
    # "a", "b" or "both" -- (a) is not confounded and can run while (b)'s de-coupling is agreed.
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    tmp = Path("/tmp/mounting_sweep")
    tmp.mkdir(parents=True, exist_ok=True)
    # ⭐ REUSE_AFTER='YYYY-MM-DD HH:MM:SS' -- points already measured at or after that moment are
    # parsed from their logs instead of re-solved.  Unset means measure everything.
    _ra = os.environ.get("REUSE_AFTER", "")
    _reuse = _dt.datetime.strptime(_ra, "%Y-%m-%d %H:%M:%S").timestamp() if _ra else 0.0
    _missed, _passed = [], []
    out = ["MOUNTING SWEEPS -- p5 -176(4).  Same path as the other sweeps: the real driver, once",
           "per point, stopped after the start-pose lines.  No route run, no reimplementation.",
           f"START_TRIES = {TRIES} draws per solve.  ⚠ The draw count is part of what the table",
           "says: 24 draws gave survivor counts that were a property of the sample, not the cell",
           "(p5 §31).  It is in the file name so two grids cannot share one path.",
           (f"⚠ points measured before {_ra} were reused from their logs, not re-solved."
            if _ra else ""), ""]

    # ⛔ The file is rewritten after EVERY point.  It used to be written once at the end, so the
    # run that stopped on point 8 destroyed the seven rows it had already measured.
    # ⛔ ...and the draw count is in EVERY name, (a) and (c) included.  The banked 24-draw tables
    # keep the names they were pinned under; a re-run at another count lands beside them instead
    # of on top of them.  A generator overwriting a pinned artifact has happened here once.
    # ⛔ OUT_TAG so a re-run under a changed driver lands beside the banked table instead of on
    # top of it.  Overwriting a pinned artifact with its own generator has happened here once.
    _out_path = HERE / ({"a": "CROWN_RADIUS_SWEEP", "b": "SPREAD_TILT_SWEEP",
                         "c": "CROWN_HEIGHT_SWEEP"}.get(which, "MOUNTING_SWEEPS")
                        + f"_TRIES{TRIES}{os.environ.get('OUT_TAG', '')}.txt")

    def _flush():
        _out_path.write_text("\n".join(out) + "\n")

    # ---------------- (a) crown radius ----------------
    # ⛔ WHERE the table was taken is part of the table.  The first crown sweep was run entirely
    # at the built tilt of 45 and I reported its result as a property of the crown; the grid then
    # showed it was a property of that row.  So the mounting this sweep sits on is read from the
    # environment and printed in the header AND on every line -- a radius column with no tilt
    # beside it is the shape of the mistake, not just how it was written up.
    _sp = os.environ.get("YOKE_SPREAD_OVERRIDE", "0.220 (built default)")
    _ti = os.environ.get("TILT_DEG_OVERRIDE", "45 (built default)")
    out.append("(a) CROWN RADIUS.  'none' removes the geometry entirely -- the lower bound p5")
    out.append(f"    asked to include.  ⛔ TAKEN AT spread={_sp}, tilt={_ti} deg -- every row")
    out.append("    below is that mounting with only the radius moving.  Nothing here is a")
    out.append("    property of the crown in general.")
    out.append("    PASS = L free >= 1 AND R free >= 1 AND the arms not interleaving.")
    out.append(f"{'crown r':>9s} {'spread':>7s} {'tilt':>5s}  {'L solved':>8s} {'L free':>7s}  "
               f"{'R solved':>8s} {'R free':>7s}   {'arms closest [mm]':>17s}  PASS?")
    # radii may be given on the command line after the "a" selector, so the boundary can be
    # resolved without re-running the coarse pass.
    _extra = [v for v in sys.argv[2:]] if len(sys.argv) > 2 else []
    radii = (_extra or ["none", "0.020", "0.050", "0.080", "0.110"]) if which in ("a", "both") else []
    _passing = []
    for r in radii:
        cnt, why, gap, who, how = one({"CROWN_R_OVERRIDE": r},
                                      tmp / f"crown_{r}_{_sp}_{_ti}.log", _reuse)
        L, R = cnt.get("L", (None, None)), cnt.get("R", (None, None))
        _trunc, _clear = _truncated(L, R, gap), _separated(L, R, gap)
        _pass = (not _trunc) and bool(L[1] and R[1] and _clear)
        _v = "PASS" if _pass else ("-- NOT MEASURED --" if _trunc else "fail")
        if _trunc:
            _missed.append(f"crown r {r}  ({how})")
        if _pass:
            _passing.append(r)
        out.append(f"{r:>9s} {_sp[:7]:>7s} {_ti[:5]:>5s}  {str(L[0]):>8s} {str(L[1]):>7s}  "
                   f"{str(R[0]):>8s} {str(R[1]):>7s}   {gap:>17s}  {_v}"
                   + ("" if _trunc else f"   [gap on: {measured_on(L, R)}]"))
        out.append(f"           L rejected against: {why.get('L', '-')}")
        _flush()
        print(f"crown {r}: L {L}  R {R}  gap {gap}  -> {_v}", flush=True)
    if radii:
        out.append("")
        if _passing:
            _num = [x for x in _passing if x != "none"]
            out.append(f"⭐ PASSING radii at this mounting: {_passing}")
            out.append(f"   -> largest radius that keeps all three conditions: "
                       f"{max(_num, key=float) if _num else 'none (only with the crown removed)'}")
            out.append(f"   ⚠ largest SWEPT, not a boundary: the limit lies between it and the "
                       f"next value up, which failed.")
        else:
            out.append("⛔ No radius at this mounting keeps all three conditions.")
    out.append("")

    # ---------------- (c) crown HEIGHT, radius derived so the head reaches the mounts -------
    if which == "c":
        out.append("(c) CROWN HEIGHT.  p5 §26-3: CROWN_Z0 is swept and the RADIUS FOLLOWS, as")
        out.append("    R = (SHOULDER_HEIGHT - CROWN_Z0)/2, so the head's top lands exactly on")
        out.append("    the mounts at every point.  ⛔ This is what the radius sweep was NOT:")
        out.append("    there a 5 mm head had its top 190 mm below the mounts and was carrying")
        out.append("    nothing.  Each row here is a head that actually reaches.")
        out.append(f"    ⛔ TAKEN AT spread={_sp}, tilt={_ti} deg.")
        out.append("    PASS = L free >= 1 AND R free >= 1 AND the arms not interleaving.")
        out.append(f"{'Z0 [m]':>7s} {'R [m]':>6s} {'top':>6s}  {'L solved':>8s} {'L free':>7s}  "
                   f"{'R solved':>8s} {'R free':>7s}   {'arms closest [mm]':>17s}  PASS?")
        _pass_z = []
        for z0 in (_extra or ["1.330", "1.380", "1.430", "1.470", "1.510"]):
            cnt, why, gap, who, how = one({"CROWN_Z0_OVERRIDE": z0},
                                          tmp / f"z_{z0}_{_sp}_{_ti}.log", _reuse)
            L, R = cnt.get("L", (None, None)), cnt.get("R", (None, None))
            _r = (1.530 - float(z0)) / 2.0
            _trunc, _clear = _truncated(L, R, gap), _separated(L, R, gap)
            _pass = (not _trunc) and bool(L[1] and R[1] and _clear)
            _v = "PASS" if _pass else ("-- NOT MEASURED --" if _trunc else "fail")
            if _trunc:
                _missed.append(f"Z0 {z0}  ({how})")
            if _pass:
                _pass_z.append(z0)
            out.append(f"{z0:>7s} {_r:6.3f} {float(z0)+2*_r:6.3f}  {str(L[0]):>8s} "
                       f"{str(L[1]):>7s}  {str(R[0]):>8s} {str(R[1]):>7s}   {gap:>17s}  {_v}"
                       + ("" if _trunc else f"   [gap on: {measured_on(L, R)}]"))
            out.append(f"           L rejected against: {why.get('L', '-')}")
            _flush()
            print(f"Z0 {z0} (R {_r:.3f}): L {L} R {R} gap {gap} -> {_v}", flush=True)
        out.append("")
        out.append(f"⭐ PASSING heights: {_pass_z or 'none'}")
        if _pass_z:
            out.append(f"   -> lowest passing underside (fattest head that still passes): "
                       f"{min(_pass_z, key=float)}  = R {(1.530-float(min(_pass_z, key=float)))/2:.3f}")
        out.append("⛔ Not a verdict.  What to build is p5's call and Rs's to settle.")
        if _missed:
            out.append(f"⛔ {len(_missed)} height(s) were NOT MEASURED: {', '.join(_missed)}")
        _flush()
        print("written")
        return 0

    # ---------------- (b) spread x tilt, with the interleave readout ----------------
    out.append("(b) YOKE_SPREAD x TILT, with the 88 mm interleave read at every point.")
    out.append("    ⛔ TWO SHEETS (p5 -177(3)): every point is run with the crown REMOVED and")
    out.append("    again with it PINNED at 0.110.  CROWN_R is normally derived as YOKE_SPREAD/2,")
    out.append("    so a single sheet would drag the crown along with the spread and could not")
    out.append("    separate 'wider shoulders helped' from 'a fatter head hurt'.")
    out.append("    ⚠ PINNED MEANS THE RADIUS ONLY.  The crown's LENGTH follows the spread by")
    out.append("    definition -- the capsule runs from -spread to +spread -- so a pinned radius")
    out.append("    is not a pinned object: wide spread gives a long thin bar, narrow spread a")
    out.append("    short fat head.  'The crown was held fixed' must not be read as 'the same")
    out.append("    body was present throughout'. (p5 -179(2))")
    out.append("    ⚠ On the pinned sheet the wide end leaves a head thinner relative to the")
    out.append("    spread than the cell's own rule gives -- the cost of isolating the variable,")
    out.append("    not a proposal about how to build one.")
    out.append("    ⚠ The spec comment records (0.22, 45) as interleaving at an 88 mm span and")
    out.append("    (0.40, 20) as clearing.  That pair is re-measured here, not argued, and both")
    out.append("    readouts are taken at every combination so neither can be lifted off a point")
    out.append("    that was measured for the other.")
    out.append("    ⭐ 'gap on' names the poses the interleave was measured at.  When an arm has no")
    out.append("    clear candidate the driver puts them all back and chooses among rejected")
    out.append("    poses, so the gap on that row is the distance between arms at a configuration")
    out.append("    that is not usable.  PASS = all three legs at ONE witness pair.")
    out.append(f"{'crown':>6s} {'spread':>7s} {'tilt':>5s}  {'L solved':>8s} {'L free':>7s}  "
               f"{'R solved':>8s} {'R free':>7s}   {'arms closest [mm]':>18s}  "
               f"{'interleaving?':>18s}  {'gap on':>13s}  ALL THREE?")
    # ⭐ p5 -177(3): every point twice -- once with the crown removed (the lower bound, column
    # only) and once at one radius held fixed for the whole sweep.  Two sheets, so "wider
    # shoulders helped" and "a fatter head hurt" cannot hide inside one number, and the 88 mm
    # readout is taken under both so the span question closes without the confound either.
    for crown in (("none", "0.110") if which in ("b", "both") else ()):
      for spread in ("0.220", "0.280", "0.340", "0.400"):
        for tilt in ("45", "30", "20"):
            # ⛔ CROWN_R is pinned across this whole grid.  In the cell it is a DERIVED quantity,
            # YOKE_SPREAD / 2, so sweeping the spread would move the crown with it and the table
            # could not tell "wider shoulders helped" from "a fatter head hurt".  p6 caught this
            # before the grid ran.  Pinning it at the built 0.110 makes spread and tilt the only
            # things moving.  ⚠ At the wide end that head is thinner RELATIVE to the spread than
            # the cell's own rule would make it -- that is the price of isolating the variable,
            # and it is not a proposal about how to build one.
            cnt, why, gap, who, how = one({"YOKE_SPREAD_OVERRIDE": spread,
                                           "TILT_DEG_OVERRIDE": tilt, "CROWN_R_OVERRIDE": crown},
                                          tmp / f"st_{crown}_{spread}_{tilt}.log", _reuse)
            L, R = cnt.get("L", (None, None)), cnt.get("R", (None, None))
            # ⛔ A truncated point gets a row that cannot be mistaken for a measurement, and the
            # grid CARRIES ON.  The first version raised here, which kept the table honest and
            # threw away the seven points already measured -- turning one slow point into a whole
            # lost run.  Refusing to REPORT a truncation and refusing to CONTINUE are different
            # things, and only the first was ever the requirement.
            if _truncated(L, R, gap):
                _missed.append(f"crown {crown} spread {spread} tilt {tilt}  ({how})")
                out.append(f"{crown:>6s} {spread:>7s} {tilt:>5s}   -- NOT MEASURED: {how}, no "
                           f"interleave line (L={L[0]} R={R[0]}) --")
                _flush()
                print(f"crown {crown} spread {spread} tilt {tilt}: NOT MEASURED", flush=True)
                continue
            inter = ("no (beyond radius)" if gap == "beyond radius" else
                     ("YES" if float(gap) <= 0 else "no"))
            _all3 = bool(L[1] and R[1] and inter.startswith("no"))
            if _all3:
                _passed.append(f"crown {crown} spread {spread} tilt {tilt}  "
                               f"L free {L[1]}  R free {R[1]}  gap {gap} mm")
            out.append(f"{crown:>6s} {spread:>7s} {tilt:>5s}  {str(L[0]):>8s} "
                       f"{str(L[1]):>7s}  {str(R[0]):>8s} {str(R[1]):>7s}   {gap:>18s}  "
                       f"{inter:>18s}  {measured_on(L, R):>13s}  "
                       f"{'PASS' if _all3 else 'fail'}" + (f"  ({who})" if who else ""))
            _flush()
            print(f"crown {crown} spread {spread} tilt {tilt}: L {L} R {R} gap {gap} -> {inter}"
                  f" -> {'PASS' if _all3 else 'fail'}", flush=True)
    if which in ("b", "both"):
        out.append("")
        out.append(f"⭐ PASSING points -- all three legs at one witness pair: {len(_passed)}")
        out.extend(f"     {p}" for p in _passed) if _passed else out.append("     -- none.")
        out.append("")
        out.append("⛔ A PASS is a WITNESS and a fail is NOT a refutation.  The interleave is read")
        out.append("   at ONE pair of poses, the chosen one.  With N clear poses on one arm and M")
        out.append("   on the other there are N x M pairs and exactly one was measured, so a")
        out.append("   touching row says the chosen pair touches -- not that the mounting has no")
        out.append("   pair that clears.  Reading = INTERLEAVE_COLUMN_READING_20260802.md.")
    if _missed:
        out.append("")
        out.append(f"⛔ {len(_missed)} point(s) were NOT MEASURED.  Nothing above is a statement")
        out.append("   about the grid as a whole:")
        out.extend(f"     {p}" for p in _missed)
    out.append("")
    out.append("⛔ Not a verdict and not a recommendation.  Both tables are the numbers p5 asked")
    out.append("   for; which mounting to take, and whether the pair constraint still binds, are")
    out.append("   p5's call and Rs's to settle.")
    _flush()
    print("written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
