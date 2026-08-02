"""Sweep the grasp pair's centre and report how many collision-free start poses each arm keeps.

p5 -169(2) asked for this and named the instrument: the per-side collision-free candidate count,
which only became readable once the silent `or cands` fallback was separated out -- before that,
"none cleared" and "all cleared" printed the same number.  The wanted output is the upper bound
on the centre's x at which the LEFT arm still keeps at least one candidate.

Method: run the real driver once per centre with GRASP_CENTRE_X set, read its own two start-pose
IK lines, and stop it as soon as they appear.  ⛔ Deliberately not a reimplementation: a copy of
the solve would be measuring the copy.  Nothing is judged here -- the numbers go back to p5.

⚠ The driver renders and would run a full episode; this kills it once the two lines are printed,
so each point costs about a minute rather than a quarter of an hour.  One process at a time.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = "/home/rlrk/env_isaaclab7/bin/python"
PAT = re.compile(r"start-pose IK ([LR]): (\d+) solved / (\d+) collision-free")
# ⚠ 240 was tuned for 24 draws.  At 240 draws a point takes about a hundred seconds with the
# collision detection out of the IK loop, and considerably longer with it in -- and a cut that
# falls between the two arms' solves writes a row that reads as a measurement.  The wait breaks
# as soon as both counts are in, so a generous cap costs nothing on a fast point.
TIMEOUT_S = int(os.environ.get('SWEEP_TIMEOUT_S', '2400'))
# The draw count is part of the table's identity: a zero from 24 draws and a zero from 240 are
# different claims.  It goes in the file name so the two cannot share a path.
TRIES = os.environ.get('START_TRIES', '24')


def one(centre: float, log: Path):
    env = dict(os.environ, GRASP_CENTRE_X=f"{centre:.6f}")
    with log.open("wb") as fh:
        # ⛔ env=env.  It was built on the line above and then not passed, so every point ran
        # the driver's default centre and the sweep measured one configuration eight times.  I
        # had already blamed a duplicate target computation for this -- that duplicate is real
        # and is fixed, but it was NOT what produced these rows, and finding *a* defect is not
        # the same as finding *the* defect.  The self-check below is what refused the second
        # attempt and sent me back here.
        p = subprocess.Popen([PY, "-u", "ur15_steps_wired.py"], cwd=HERE, env=env,
                             stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        got, t0 = {}, time.time()
        while time.time() - t0 < TIMEOUT_S:
            if p.poll() is not None:
                break
            for line in log.read_text(errors="replace").splitlines():
                mm = PAT.search(line)
                if mm:
                    got[mm.group(1)] = (int(mm.group(2)), int(mm.group(3)))
            if len(got) == 2:
                break
            time.sleep(2.0)
        if p.poll() is None:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            p.wait(timeout=30)
    txt = log.read_text(errors="replace")
    for line in txt.splitlines():
        mm = PAT.search(line)
        if mm:
            got[mm.group(1)] = (int(mm.group(2)), int(mm.group(3)))
    held = re.search(r"measured grasp: L=cab(\d+) \[([-\d. ]+)\]\s+R=cab(\d+) \[([-\d. ]+)\]", txt)
    return got, held


def main() -> int:
    centres = [float(v) for v in sys.argv[1:]] or \
        [0.150, 0.120, 0.090, 0.060, 0.030, 0.000, -0.030, -0.060]
    tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "grasp_centre_sweep"
    tmp.mkdir(parents=True, exist_ok=True)
    rows = []
    print(f"{'centre x [m]':>12s}  {'L solved':>8s} {'L free':>7s}  {'R solved':>8s} {'R free':>7s}"
          f"   held links")
    missed = []
    for c in centres:
        got, held = one(c, tmp / f"c_{c:+.3f}.log")
        L, R = got.get("L", (None, None)), got.get("R", (None, None))
        hl = (f"L=cab{held.group(1)} R=cab{held.group(3)}" if held else "-")
        # ⛔ A point that did not finish is NOT a row of numbers.  Printing str(None) in the count
        # columns puts a truncation and a measurement in the same shape, which is the defect this
        # whole morning was about -- so it is recorded as missing and the sweep carries on.
        if L[0] is None or R[0] is None:
            missed.append(c)
            rows.append((c, L, R, hl))
            print(f"{c:12.3f}  -- NOT MEASURED (L={L[0]} R={R[0]}) --", flush=True)
            continue
        rows.append((c, L, R, hl))
        print(f"{c:12.3f}  {str(L[0]):>8s} {str(L[1]):>7s}  {str(R[0]):>8s} {str(R[1]):>7s}   {hl}",
              flush=True)

    # ⛔ Does this sweep vary anything?  The first attempt returned eight identical rows because a
    # SECOND copy of the target computation still read C1's x and silently won.  Eight identical
    # rows are what a working sweep of a flat landscape looks like AND what a sweep that never
    # moved looks like, so the run is refused unless the held links actually differ.
    distinct = {hl for _, _, _, hl in rows}
    moved = sum(1 for c, *_ in rows if abs(c - rows[0][0]) > 1e-12)
    if moved and len(distinct) == 1:
        raise RuntimeError(
            f"the centre was swept over {len(rows)} values and the links held never changed "
            f"({distinct.pop()}).  That is not a flat landscape, it is a sweep that did not move: "
            f"a centre 210 mm away cannot hold the same 15 mm cable link.  Refusing to report "
            f"numbers that would read as eight measurements of eight configurations.")

    ok = [c for c, L, R, _ in rows if L[1] is not None and L[1] >= 1]
    rows = [r for r in rows if r[1][0] is not None]   # truncated points carry no numbers
    out = [
        "GRASP-CENTRE SWEEP -- collision-free start poses per arm, by where the pair sits",
        "instrument: the driver's own start-pose IK line, with the silent or-cands fallback",
        "            separated out (before that fix, 'none cleared' and 'all cleared' printed",
        "            the same number and this sweep could not have been read)",
        "method    : the real driver, once per centre, GRASP_CENTRE_X set, stopped as soon as it",
        "            has printed both lines.  No reimplementation of the solve.",
        "⚠ span    : 88 mm COMMANDED; the links actually taken sit 75 mm apart, because the cable",
        "            is 15 mm segments and the nearest link is what gets held.",
        "",
        f"{'centre x [m]':>12s}  {'L solved':>8s} {'L free':>7s}  {'R solved':>8s} {'R free':>7s}"
        f"   held links",
    ]
    for c, L, R, hl in rows:
        out.append(f"{c:12.3f}  {str(L[0]):>8s} {str(L[1]):>7s}  {str(R[0]):>8s} {str(R[1]):>7s}"
                   f"   {hl}")
    out.append("")
    if ok:
        out.append(f"LEFT ARM keeps >=1 collision-free candidate at centre x in {sorted(ok)}")
        out.append(f"  -> highest swept centre x with a left-arm candidate: {max(ok):+.3f} m")
        out.append(f"  ⚠ this is the highest value SWEPT, not a boundary: the true upper bound "
                   f"lies between {max(ok):+.3f} and the next value up that failed.")
    else:
        out.append("⛔ LEFT ARM keeps ZERO collision-free candidates at every centre swept.")
    out.append("⛔ Not a verdict and not a recommendation: where the pair should sit is p5's call.")
    if missed:
        out.append("")
        out.append(f"⛔ {len(missed)} centre(s) NOT MEASURED: {missed} -- nothing above is a "
                   f"statement about the sweep as a whole.")
    out.insert(1, f"START_TRIES = {TRIES} draws per solve.  ⚠ A survivor count of zero from 24 "
                  f"draws does not mean no clear pose exists -- four of sixteen such zeros in "
                  f"the mounting grid became non-zero at 240 (GRID_24_VS_240_20260802.txt).")
    # ⛔ OUT_TAG so a partial re-run (a boundary bisection, say) lands beside the banked
    # table instead of overwriting a pinned artifact with a subset of its own rows.
    (HERE / f"GRASP_CENTRE_SWEEP_TRIES{TRIES}{os.environ.get('OUT_TAG', '')}.txt").write_text("\n".join(out) + "\n")
    print("\n".join(out[-4:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
