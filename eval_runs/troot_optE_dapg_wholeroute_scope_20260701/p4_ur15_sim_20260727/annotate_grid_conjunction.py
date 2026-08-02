"""Read the grid's own per-point logs back and say, per point, WHAT THE GAP WAS MEASURED ON.

⛔ Why this exists.  The (b) table prints `arms closest [mm]` and `interleaving?` in the same two
columns whether the two arms were at CLEAR start poses or at poses the clearance test had
rejected.  When an arm has zero collision-free candidates the driver puts them all back and picks
among rejected poses -- it says so, loudly -- and the interleave is then measured on a
configuration the first column says does not exist.  Two different quantities, one column.

That matters most exactly where the sweep is most useful: the spec comment's claim is about the
88 mm interleave alone, so a reader lifting the interleave column off a row is lifting a number
whose meaning depends on a column they were not looking at.

⚠ This does NOT change any conjunction verdict.  A row with L free = 0 fails the conjunction on
its first leg no matter what the gap says.  What the marker changes is whether the gap on that
row may be read on its own.

⛔ NO RE-RUN.  Everything here comes from the logs the sweep already wrote.

⛔ STALE-LOG GUARD.  /tmp/mounting_sweep still holds the 24-draw run's logs at exactly the same
filenames.  A point this run has not reached yet has a log that looks identical in shape and is
a different measurement -- the same failure the truncation guard was added for.  So every log is
required to be newer than the run's start, given on the command line, and a point whose log is
older is reported as NOT REACHED rather than read.
"""

from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = Path("/tmp/mounting_sweep")
CNT = re.compile(r"start-pose IK ([LR]): (\d+) solved / (\d+) collision-free")
PUTBACK = re.compile(r"start-pose IK ([LR]): NOT ONE of (\d+) candidates cleared")
ILV = re.compile(r"88mm-SPAN INTERLEAVE: arms closest ([-+\d.]+) mm \(([^)]*)\)|"
                 r"88mm-SPAN INTERLEAVE: arms closest (nothing within[^ ]* \d+ mm[^ ]* radius)")

CROWNS = ("none", "0.110")
SPREADS = ("0.220", "0.280", "0.340", "0.400")
TILTS = ("45", "30", "20")


def read_point(path: Path, floor: float):
    if not path.exists():
        return None, "no log"
    if path.stat().st_mtime < floor:
        stamp = _dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M")
        return None, f"NOT REACHED (log is from {stamp}, before this run)"
    txt = path.read_text(errors="replace")
    cnt = {m[0]: (int(m[1]), int(m[2])) for m in CNT.findall(txt)}
    back = {m[0] for m in PUTBACK.findall(txt)}
    mm = ILV.search(txt)
    gap = mm.group(1) if mm and mm.group(1) else ("beyond radius" if mm else "?")
    who = mm.group(2) if mm and mm.group(2) else ""
    return (cnt, back, gap, who), ""


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: annotate_grid_conjunction.py 'YYYY-MM-DD HH:MM:SS'   (the run's start)")
        return 2
    floor = _dt.datetime.strptime(sys.argv[1], "%Y-%m-%d %H:%M:%S").timestamp()

    out = ["GRID 240 -- the conjunction, with what each interleave reading was measured on",
           f"logs required newer than {sys.argv[1]} (the run's start); anything older is the",
           "24-draw run's log at the same filename and is reported as NOT REACHED, not read.",
           "",
           "PASS = L free >= 1 AND R free >= 1 AND the arms not interleaving -- all three.",
           "⭐ 'gap on' names the poses the 88 mm interleave was measured at.  'L put back' means",
           "   the left arm had no clear candidate and the driver chose among rejected poses, so",
           "   the gap on that row is the distance between arms at a configuration that is not",
           "   usable.  The conjunction already fails there; the marker is about whether the",
           "   interleave column may be read on its own.",
           ""]
    hdr = (f"{'crown':>6s} {'spread':>7s} {'tilt':>5s}  {'L solved':>8s} {'L free':>7s}  "
           f"{'R solved':>8s} {'R free':>7s}  {'gap [mm]':>14s}  {'interleave':>10s}  "
           f"{'gap on':>14s}  ALL THREE?")
    out.append(hdr)
    rows, missing = [], []
    for crown in CROWNS:
        for spread in SPREADS:
            for tilt in TILTS:
                got, err = read_point(LOGS / f"st_{crown}_{spread}_{tilt}.log", floor)
                if got is None:
                    missing.append((crown, spread, tilt, err))
                    out.append(f"{crown:>6s} {spread:>7s} {tilt:>5s}  {err}")
                    continue
                cnt, back, gap, _who = got
                L, R = cnt.get("L", (None, None)), cnt.get("R", (None, None))
                try:
                    inter = "YES" if float(gap) <= 0 else "no"
                except ValueError:
                    inter = "no (beyond r)"
                on = {(): "both clear", ("L",): "L put back", ("R",): "R put back",
                      ("L", "R"): "both put back"}[tuple(sorted(back))]
                ok = bool(L[1] and R[1] and inter.startswith("no"))
                rows.append((crown, spread, tilt, L, R, gap, inter, on, ok))
                out.append(f"{crown:>6s} {spread:>7s} {tilt:>5s}  {str(L[0]):>8s} "
                           f"{str(L[1]):>7s}  {str(R[0]):>8s} {str(R[1]):>7s}  {gap:>14s}  "
                           f"{inter:>10s}  {on:>14s}  {'PASS' if ok else 'fail'}")
    out.append("")

    # ⛔ The sheet is not allowed to look complete when it is not.
    if missing:
        out.append(f"⛔ {len(missing)} of {len(CROWNS)*len(SPREADS)*len(TILTS)} points are NOT in "
                   f"this sheet.  Nothing below is a statement about the grid as a whole.")
    passing = [r for r in rows if r[8]]
    out.append(f"⭐ PASSING points (all three legs): {len(passing)} of {len(rows)} read")
    for c, s, t, L, R, gap, _i, _on, _ in passing:
        out.append(f"     crown {c}  spread {s}  tilt {t}   L free {L[1]}  R free {R[1]}  "
                   f"gap {gap} mm")
    if not passing and rows:
        out.append("     -- none.")

    clean = [r for r in rows if r[7] == "both clear"]
    out.append("")
    out.append(f"⭐ The interleave column may be read on its own on {len(clean)} of {len(rows)} "
               f"rows (both arms clear).  On the rest an arm was put back.")
    for c, s, t, _L, _R, gap, inter, _on, _ in clean:
        out.append(f"     crown {c}  spread {s}  tilt {t}   gap {gap} mm   interleaving: {inter}")
    out.append("")
    out.append("⛔ Not a verdict and not a recommendation.  Which mounting to build is p5's call")
    out.append("   and Rs's to settle.")
    (HERE / "GRID240_CONJUNCTION_20260802.txt").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
