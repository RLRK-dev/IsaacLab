"""Move the whole work row away from the column in y, and read what still rejects the arms.

p5 -175(2).  Two options are left -- change the mounting, or move the work row -- and this is the
measurement that separates them: if the left arm's collision-free count rises with y, moving the
row is alive; if it stays at zero, the mounting is what is left.

⚠ The row moves as one set.  REST_Y places the cable AND the saddle posts, the clip rows sit at
fixed offsets from it, and the table is derived from both -- so a single knob shifts REST_Y and
the two clip rows by the same amount and lets the table follow by construction.  Moving one of
them alone would be changing two things and calling it one.

Same path as the x sweep: the real driver, once per y, stopped as soon as it has printed the
start-pose lines.  ⛔ No reimplementation of the solve, and no route run.
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
# ⚠ 240 was tuned for 24 draws.  A cap that falls between the two arms' solves writes a row
# that reads as a measurement; the wait breaks as soon as both counts are in, so a generous
# cap costs nothing on a fast point.
TIMEOUT_S = int(os.environ.get('SWEEP_TIMEOUT_S', '2400'))
# A zero from 24 draws and a zero from 240 are different claims -- the draw count goes in the
# file name.  (The grasp-centre sweep's 24-draw zeros turned out to be the sample at three of
# its centres; GRASP_CENTRE_240_READING_20260802.md.)
TRIES = os.environ.get('START_TRIES', '24')


def one(dy: float, log: Path):
    env = dict(os.environ, WORK_ROW_DY=f"{dy:.6f}")
    with log.open("wb") as fh:
        p = subprocess.Popen([PY, "-u", "ur15_steps_wired.py"], cwd=HERE, env=env,
                             stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        t0 = time.time()
        while time.time() - t0 < TIMEOUT_S and p.poll() is None:
            if len(CNT.findall(log.read_text(errors="replace"))) >= 2:
                break
            time.sleep(2.0)
        if p.poll() is None:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            p.wait(timeout=30)
    txt = log.read_text(errors="replace")
    cnt = {m[0]: (int(m[1]), int(m[2])) for m in CNT.findall(txt)}
    why = {m[0]: m[1] for m in WHY.findall(txt)}
    # read the cable's OWN settled y back out of the run -- the knob is only believed if the
    # cell it produced actually moved.  (The first version of this regex had an alternation that
    # matched something else first and returned "?", which would have disarmed the self-check.)
    row = re.search(r"cable settled: x\[[^\]]*\] y\[([-+\d.]+)", txt)
    return cnt, why, (row.group(1) if row else "")


def main() -> int:
    dys = [float(v) for v in sys.argv[1:]] or [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    tmp = Path("/tmp/work_row_y_sweep")
    tmp.mkdir(parents=True, exist_ok=True)
    rows, out, missed = [], [], []
    print(f"{'dy [m]':>7s} {'row y':>7s}  {'L solved':>8s} {'L free':>7s}  {'R solved':>8s} "
          f"{'R free':>7s}")
    for dy in dys:
        cnt, why, ry = one(dy, tmp / f"y_{dy:+.3f}.log")
        L, R = cnt.get("L", (None, None)), cnt.get("R", (None, None))
        rows.append((dy, L, R, why.get("L", "-"), why.get("R", "-"), ry))
        # ⛔ A point that did not finish is not a row of numbers: str(None) in the count columns
        # gives a truncation the shape of a measurement.
        if L[0] is None or R[0] is None:
            missed.append(dy)
            print(f"{dy:7.3f} {ry or '?':>7s}  -- NOT MEASURED (L={L[0]} R={R[0]}) --", flush=True)
            continue
        print(f"{dy:7.3f} {ry or '?':>7s}  {str(L[0]):>8s} {str(L[1]):>7s}  {str(R[0]):>8s} "
              f"{str(R[1]):>7s}", flush=True)

    # ⛔ Same self-check as the x sweep, for the same reason: a sweep that did not move looks
    # exactly like a flat landscape.  The cable's own settled y is read back from the run.
    ys = {r[5] for r in rows}
    if len(rows) > 1 and len(ys) == 1:
        raise RuntimeError(f"the row was swept over {len(rows)} offsets and the cable settled at "
                           f"the same y every time ({ys.pop()}) -- the knob did not reach the "
                           f"cell.  Refusing to report.")

    out.append("WORK-ROW y SWEEP -- what still rejects each arm as the row moves off the column")
    out.append("p5 -175(2): separates 'change the mounting' from 'move the work row'.")
    out.append("⚠ one set: REST_Y and both clip rows shift together; the table is derived and")
    out.append("   follows.  Relative spacing is untouched at every point.")
    out.append("method: the real driver, once per offset, stopped after the start-pose lines.")
    out.append("")
    out.append(f"{'dy [m]':>7s} {'cable y':>8s}  {'L solved':>8s} {'L free':>7s}  "
               f"{'R solved':>8s} {'R free':>7s}")
    for dy, L, R, _, _, ry in rows:
        out.append(f"{dy:7.3f} {ry or '?':>8s}  {str(L[0]):>8s} {str(L[1]):>7s}  "
                   f"{str(R[0]):>8s} {str(R[1]):>7s}")
    out.append("")
    out.append("REJECTED AGAINST, per offset (⚠ one pose can appear under two names: the arm test")
    out.append("and the mast test run independently, so the counts do not partition the poses)")
    for dy, _, _, wl, wr, _ in rows:
        out.append(f"  dy {dy:+.3f}  L: {wl}")
        out.append(f"  dy {dy:+.3f}  R: {wr}")
    out.append("")
    lift = [dy for dy, L, _, _, _, _ in rows if L[1] is not None and L[1] >= 1]
    if lift:
        out.append(f"⭐ The LEFT arm's clear count rises above zero at dy = {min(lift):+.3f} m and "
                   f"stays measurable at {sorted(lift)}.")
        out.append("   -> moving the work row is not dead; the boundary lies between that offset "
                   "and the one below it.")
    else:
        out.append("⛔ The LEFT arm keeps ZERO collision-free candidates at every offset swept.")
    out.append("⛔ Not a verdict.  Which option to take is p5's call and Rs's to settle.")
    if missed:
        out.append(f"⛔ {len(missed)} offset(s) NOT MEASURED: {missed}")
    out.insert(1, f"START_TRIES = {TRIES} draws per solve.  ⚠ A zero from 24 draws does not mean "
                  f"no clear pose exists.")
    (HERE / f"WORK_ROW_Y_SWEEP_TRIES{TRIES}.txt").write_text("\n".join(out) + "\n")
    print("\n".join(out[-3:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
