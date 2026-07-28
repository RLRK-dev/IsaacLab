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
TIMEOUT_S = 260


def one(env_extra: dict, log: Path):
    env = dict(os.environ, **{k: str(v) for k, v in env_extra.items()})
    with log.open("wb") as fh:
        p = subprocess.Popen([PY, "-u", "ur15_steps_wired.py"], cwd=HERE, env=env,
                             stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        t0 = time.time()
        while time.time() - t0 < TIMEOUT_S and p.poll() is None:
            if "88mm-SPAN INTERLEAVE" in log.read_text(errors="replace"):
                break
            time.sleep(2.0)
        if p.poll() is None:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            p.wait(timeout=30)
    txt = log.read_text(errors="replace")
    cnt = {m[0]: (int(m[1]), int(m[2])) for m in CNT.findall(txt)}
    why = {m[0]: m[1] for m in WHY.findall(txt)}
    mm = ILV.search(txt)
    gap = mm.group(1) if mm and mm.group(1) else ("beyond radius" if mm else "?")
    who = mm.group(2) if mm and mm.group(2) else ""
    return cnt, why, gap, who


def main() -> int:
    # "a", "b" or "both" -- (a) is not confounded and can run while (b)'s de-coupling is agreed.
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    tmp = Path("/tmp/mounting_sweep")
    tmp.mkdir(parents=True, exist_ok=True)
    out = ["MOUNTING SWEEPS -- p5 -176(4).  Same path as the other sweeps: the real driver, once",
           "per point, stopped after the start-pose lines.  No route run, no reimplementation.", ""]

    # ---------------- (a) crown radius ----------------
    out.append("(a) CROWN RADIUS.  'none' removes the geometry entirely -- the lower bound p5")
    out.append("    asked to include.  Default is 0.110 = YOKE_SPREAD/2.")
    out.append(f"{'crown r':>9s}  {'L solved':>8s} {'L free':>7s}  {'R solved':>8s} {'R free':>7s}"
               f"   arms closest [mm]")
    radii = ["none", "0.020", "0.050", "0.080", "0.110"] if which in ("a", "both") else []
    for r in radii:
        cnt, why, gap, who = one({"CROWN_R_OVERRIDE": r}, tmp / f"crown_{r}.log")
        L, R = cnt.get("L", (None, None)), cnt.get("R", (None, None))
        out.append(f"{r:>9s}  {str(L[0]):>8s} {str(L[1]):>7s}  {str(R[0]):>8s} {str(R[1]):>7s}"
                   f"   {gap}")
        out.append(f"           L rejected against: {why.get('L', '-')}")
        print(f"crown {r}: L {L}  R {R}  gap {gap}", flush=True)
    out.append("")

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
    out.append(f"{'crown':>6s} {'spread':>7s} {'tilt':>5s}  {'L solved':>8s} {'L free':>7s}  "
               f"{'R solved':>8s} {'R free':>7s}   {'arms closest [mm]':>18s}  interleaving?")
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
            cnt, why, gap, who = one({"YOKE_SPREAD_OVERRIDE": spread, "TILT_DEG_OVERRIDE": tilt,
                                      "CROWN_R_OVERRIDE": crown},
                                     tmp / f"st_{crown}_{spread}_{tilt}.log")
            L, R = cnt.get("L", (None, None)), cnt.get("R", (None, None))
            try:
                inter = "YES" if float(gap) <= 0 else "no"
            except ValueError:
                inter = "no (beyond radius)"
            out.append(f"{crown:>6s} {spread:>7s} {tilt:>5s}  {str(L[0]):>8s} "
                       f"{str(L[1]):>7s}  {str(R[0]):>8s} {str(R[1]):>7s}   {gap:>18s}  {inter}"
                       + (f"  ({who})" if who else ""))
            print(f"crown {crown} spread {spread} tilt {tilt}: L {L} R {R} gap {gap} -> {inter}",
                  flush=True)
    out.append("")
    out.append("⛔ Not a verdict and not a recommendation.  Both tables are the numbers p5 asked")
    out.append("   for; which mounting to take, and whether the pair constraint still binds, are")
    out.append("   p5's call and Rs's to settle.")
    _name = {"a": "CROWN_RADIUS_SWEEP", "b": "SPREAD_TILT_SWEEP"}.get(which, "MOUNTING_SWEEPS")
    (HERE / f"{_name}_20260729.txt").write_text("\n".join(out) + "\n")
    print("written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
