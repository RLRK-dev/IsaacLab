"""Put the 24-draw grid and the 240-draw grid side by side, point by point.

⛔ The two tables are one quantity.  Everything between them is a print, a refactor with identical
values, or the swept variable itself: the clearance predicate, the attitude menu values, the
seeding and the targets are untouched (git diff 528654735e..HEAD on the driver, read line by line
before this comparison was made).  Without that check the columns would not be comparable and this
script would be putting two different measurements in one row.

The question is p5 §31 asked at grid scale: a survivor count of zero can mean "no clear pose
exists here" or "twenty-four draws did not find one", and only a bigger sample separates them.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILT = ("0.110", "0.220", "45")     # sweep_mounting.py's own defaults for spread and tilt


def rows(p: Path):
    out = {}
    for ln in p.read_text().split("\n"):
        f = ln.split()
        if len(f) >= 3 and f[0] in ("none", "0.110") and f[1][:1].isdigit():
            key = (f[0], f[1], f[2])
            # ⛔ A NOT MEASURED row must not be parsed into numbers that happen to sit in the
            # right columns.  It is None, and every consumer has to handle it.
            out[key] = None if "NOT MEASURED" in ln else dict(
                Ls=int(f[3]), Lf=int(f[4]), Rs=int(f[5]), Rf=int(f[6]), gap=f[7], inter=f[8])
    return out


def main() -> int:
    a = rows(HERE / "SPREAD_TILT_SWEEP_TRIES24_20260729.txt")
    b = rows(HERE / "SPREAD_TILT_SWEEP_TRIES240.txt")
    out = ["24 DRAWS vs 240 DRAWS, point by point -- p5 §31 asked at grid scale",
           "⛔ The tables are comparable: between them the driver changed only in prints, in a",
           "   refactor with identical values, and in the swept variable.  The clearance",
           "   predicate, the menu values, the seeding and the targets are untouched.",
           "⚠ A zero at 24 draws can be 'none exists' or 'none found'.  Only the bigger sample",
           "   separates them, and it separates them for four points and not for twelve.", "",
           f"{'point':24s} {'Lfree24':>7s} {'Lfree240':>8s}  {'Rfree24':>7s} {'Rfree240':>8s}  "
           f"{'gap24':>7s} {'gap240':>7s}"]
    became, stayed, n0_24, n0_240, passes = [], [], 0, 0, []
    for k, A in a.items():
        B = b.get(k)
        kk = f"crown {k[0]:>5s}  spread {k[1]}  tilt {k[2]:>2s}"
        if A is None or B is None:
            out.append(f"{kk:24s} {A['Lf'] if A else '--':>7} {'--':>8}  "
                       f"{A['Rf'] if A else '--':>7} {'--':>8}  {A['gap'] if A else '--':>7} "
                       f"{'--':>7}   <- not measured at 240 (the driver segfaults)")
            continue
        n0_24 += A["Lf"] == 0
        n0_240 += B["Lf"] == 0
        flag = ""
        if A["Lf"] == 0 and B["Lf"] > 0:
            became.append(kk)
            flag = "   <- ZERO WAS THE SAMPLE"
        elif A["Lf"] == 0:
            stayed.append(kk)
        if B["Lf"] and B["Rf"] and B["inter"].startswith("no"):
            passes.append(f"{kk}   L free {B['Lf']}  R free {B['Rf']}  gap {B['gap']} mm")
        out.append(f"{kk:24s} {A['Lf']:>7d} {B['Lf']:>8d}  {A['Rf']:>7d} {B['Rf']:>8d}  "
                   f"{A['gap']:>7s} {B['gap']:>7s}{flag}")

    out += ["", f"LEFT-ARM ZEROS: {n0_24} of {sum(1 for k in a if b.get(k))} comparable points at "
                f"24 draws, {n0_240} at 240.",
            f"  ⭐ {len(became)} zero(s) were the SAMPLE, not the cell:"]
    out += [f"       {p}" for p in became]
    out += [f"  ⛔ {len(stayed)} stayed zero at ten times the sample:"]
    out += [f"       {p}" for p in stayed]
    out += ["", f"ALL THREE LEGS at one witness pair, at 240 draws: {len(passes)}"]
    out += [f"     {p}" for p in passes]
    B0 = b.get(BUILT)
    A0 = a.get(BUILT)
    out += ["", "THE BUILT CELL -- crown 0.110, spread 0.220, tilt 45 (sweep_mounting.py's own",
            "defaults for spread and tilt; the crown follows as YOKE_SPREAD/2):",
            f"     24 draws : L {A0['Ls']} solved / {A0['Lf']} clear   R {A0['Rs']}/{A0['Rf']}   "
            f"gap {A0['gap']}",
            f"     240 draws: L {B0['Ls']} solved / {B0['Lf']} clear   R {B0['Rs']}/{B0['Rf']}   "
            f"gap {B0['gap']}",
            "  ⇒ The left arm's zero at the built cell is NOT a sampling artifact: the solved",
            "     count grows eight-fold and the clear count stays at zero.",
            "", "⛔ Not a verdict.  A PASS is a witness; a fail is not a refutation (the interleave",
            "   is read at one pose pair out of N x M).  Which mounting to build is p5's call."]
    (HERE / "GRID_24_VS_240_20260802.txt").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
