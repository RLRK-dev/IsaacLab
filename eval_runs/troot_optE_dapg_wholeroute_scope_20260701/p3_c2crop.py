#!/usr/bin/env python3
"""P3 C2-inspection crop (W0-d J6, %12/%9 approved 14:00).

Per cell, from the final settle frame of the built-in 7-cam montage (--record-video), produce a labeled
inspection image with the 2 discrimination views (%9 rider r2):
  - overhead (top-down): cable vs C2 clip MOUTH + the -x wall   -> r2(ii) outside the mouth?
  - front Y-Z: cable Z-HEIGHT above the C2 clip (perch vs seat) -> r2(i) wall-top (>=5mm) vs floor+1.7mm?
  - C2-zoom: tighter crop on the C2 clip within the front view.
RENDER != VERDICT — the seat call is %12+%9 joint frame-check; this only frames the evidence.
0-commit (result dir). Copies the overview + x-20_y-15 to ~/Downloads (Rs visual, memory rule).
"""
import csv
import glob
import os
import shutil

import numpy as np
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__)) + "/p3_grid"
# %12-confirmed 7 cells, in z_gap order (floor -> extreme) for the overview.
CELLS = ["x0_y10", "x5_y20", "x15_y5", "x0_y-20", "x-15_y15", "x-20_y-15", "x-20_y5"]
PW = 490  # montage = 7 even panels over W=3430
OH_BOX = (3 * PW, 0, 4 * PW, 450)     # panel3 overhead (top-down C1+C2 + cable path)
FR_BOX = (4 * PW, 0, 5 * PW, 450)     # panel4 front Y-Z (C1 seat + guide toward C2)
C2Z_BOX = (2150, 295, 2360, 470)      # C2 clip + cable-above, within the front panel


def _cyan_centroid(im, box):
    """Locate the C2 clip (cyan rgba[.10,.70,.92]*1.3 exposure) within a panel box -> (x,y) in montage coords."""
    a = np.array(im.crop(box).convert("RGB")).astype(int)
    m = (a[:, :, 2] > 190) & (a[:, :, 1] > 150) & (a[:, :, 0] < 110)
    if m.sum() < 30:
        return None
    ys, xs = np.where(m)
    return (box[0] + int(xs.mean()), box[1] + int(ys.mean()))


def _row(tag):
    p = os.path.join(BASE, "p3_grid_summary.csv")
    if os.path.isfile(p):
        for r in csv.DictReader(open(p)):
            if r["tag"] == tag:
                return r
    return {}


def inspect(tag):
    d = os.path.join(BASE, f"render_{tag}")
    frames = sorted(glob.glob(os.path.join(d, "_route_frames", "*.png")))
    if not frames:
        return None
    im = Image.open(frames[-1]).convert("RGB")
    r = _row(tag)
    zg, vd, cls = r.get("c2z_gap_mm", "?"), r.get("verdict", "?"), r.get("cls", "?")
    oh = im.crop(OH_BOX).resize((620, 570), Image.LANCZOS)
    fr = im.crop(FR_BOX).resize((620, 570), Image.LANCZOS)
    cc = _cyan_centroid(im, FR_BOX)  # auto-center the C2 zoom on the cyan clip in the front panel
    if cc:
        cx, cy = cc
        z = (max(FR_BOX[0], cx - 105), max(0, cy - 95), min(FR_BOX[2], cx + 105), min(450, cy + 95))
    else:
        z = C2Z_BOX
    c2 = im.crop(z).resize((430, 380), Image.LANCZOS)
    out = Image.new("RGB", (oh.width + fr.width + c2.width + 40, 630), (15, 15, 15))
    out.paste(oh, (5, 55))
    out.paste(fr, (oh.width + 20, 55))
    out.paste(c2, (oh.width + fr.width + 35, 55))
    dr = ImageDraw.Draw(out)
    dr.text((8, 6), f"{tag}   cls={cls}   verdict={vd}   c2z_gap={zg}mm   (final settle frame)", fill=(255, 255, 120))
    dr.text((8, 26), "RENDER != VERDICT  —  seat call = %12+%9 joint frame-check", fill=(255, 150, 150))
    dr.text((10, 44), "OVERHEAD top-down: cable vs C2 MOUTH + -x wall  [r2(ii)]", fill=(150, 220, 255))
    dr.text((oh.width + 25, 44), "FRONT Y-Z: cable Z-HEIGHT vs C2 clip (perch?)  [r2(i)]", fill=(150, 220, 255))
    dr.text((oh.width + fr.width + 40, 44), "C2 zoom", fill=(150, 220, 255))
    out.save(os.path.join(d, "c2_inspect.png"))
    return out


def main():
    dl = os.path.expanduser("~/Downloads")
    panels, done = [], []
    for tag in CELLS:
        p = inspect(tag)
        if p is not None:
            panels.append((tag, p))
            done.append(tag)
    if not panels:
        print("no rendered cells yet")
        return
    # stacked overview (all cells, z_gap order)
    W = max(p.width for _, p in panels)
    H = sum(p.height for _, p in panels) + 10 * len(panels)
    ov = Image.new("RGB", (W, H), (0, 0, 0))
    y = 0
    for _, p in panels:
        ov.paste(p, (0, y))
        y += p.height + 10
    ov_path = os.path.join(BASE, "P3_RENDER_C2_INSPECT_ALL.png")
    ov.save(ov_path)
    # ~/Downloads copies: overview + the decision cell + its wide overhead (already in its inspect)
    if os.path.isdir(dl):
        shutil.copy(ov_path, os.path.join(dl, "P3_RENDER_C2_INSPECT_ALL.png"))
        for tag in ("x-20_y-15", "x-20_y5"):
            src = os.path.join(BASE, f"render_{tag}", "c2_inspect.png")
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(dl, f"p3_c2_inspect_{tag}.png"))
            mp4 = os.path.join(BASE, f"render_{tag}", "route_c1_to_c2.mp4")
            if os.path.isfile(mp4):
                shutil.copy(mp4, os.path.join(dl, f"p3_route_{tag}.mp4"))
    print(f"rendered+cropped {len(done)}/{len(CELLS)}: {done}")
    print(f"[written] {ov_path} (+ ~/Downloads overview + x-20_y-15/x-20_y5 inspect+mp4)")


if __name__ == "__main__":
    main()
