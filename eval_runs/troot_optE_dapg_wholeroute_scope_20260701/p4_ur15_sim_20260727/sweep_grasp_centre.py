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
TIMEOUT_S = 240


def one(centre: float, log: Path):
    env = dict(os.environ, GRASP_CENTRE_X=f"{centre:.6f}")
    with log.open("wb") as fh:
        p = subprocess.Popen([PY, "-u", "ur15_steps_wired.py"], cwd=HERE,
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
    for c in centres:
        got, held = one(c, tmp / f"c_{c:+.3f}.log")
        L, R = got.get("L", (None, None)), got.get("R", (None, None))
        hl = (f"L=cab{held.group(1)} R=cab{held.group(3)}" if held else "-")
        rows.append((c, L, R, hl))
        print(f"{c:12.3f}  {str(L[0]):>8s} {str(L[1]):>7s}  {str(R[0]):>8s} {str(R[1]):>7s}   {hl}",
              flush=True)

    ok = [c for c, L, R, _ in rows if L[1] is not None and L[1] >= 1]
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
    (HERE / "GRASP_CENTRE_SWEEP_20260729.txt").write_text("\n".join(out) + "\n")
    print("\n".join(out[-4:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
