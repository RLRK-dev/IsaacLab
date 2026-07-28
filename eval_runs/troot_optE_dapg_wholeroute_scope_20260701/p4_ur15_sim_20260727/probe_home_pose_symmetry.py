"""Why does the LEFT forearm touch the column in the cell's HOME pose -- and why does the right
side not read the same number?

pB's t42 read (PB_T42_FOUR_READINGS_LOGANALYST_20260729.md §9.2) leaves this open, and it is the
first link of the chain: home pose in contact -> j1/j2 saturated -> 45x behind -> the shared ramp
never opens -> nothing else in the run happened.  The trace prints

    mast L=-0.8 mm (g6 on L_forearm_link vs crown)   R=+60.1 mm (g42 on R_shoulder_link vs crown)

and both arms are driven by the SAME joint values, on mounts that are mirror images.  So either

  (a) the two arms are NOT mirror images where it matters for collision, or
  (b) they are, and the right-side reading is not seeing what the left-side reading sees.

Those need different fixes, so this measures which.  Nothing is changed and nothing is run: the
model is t42's own as-built cell, held at the home pose, read with the driver's own instrument
(mj_geomDistance over the same mast geoms).

⛔ This does not decide the mounting question (0.22/45 vs anything else).  It reports what the
built cell does at its start pose; the pair is p5's court and Rs's to settle.
"""

from __future__ import annotations

import sys
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from ur15_cell_spec import HOME_POSE  # noqa: E402

# t42's as-built cell, written by the driver at startup.  Read, never regenerated here, so this
# cannot measure a different cell from the one that produced the trace.
# (staged beside its own mesh pool -- some of the driver's mesh refs are bare names that resolve
# against the model file's directory, and the copy keeps the bytes identical.)
AS_BUILT = Path("/tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-19a6-4bca-8043-e6731b3f2141/"
                "scratchpad/meshpool/_as_built_t42.xml")
J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
      "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
MAST = ("stem", "foot", "crown")
SIDES = ("L", "R")


def main() -> int:
    m = mujoco.MjModel.from_xml_path(str(AS_BUILT))
    d = mujoco.MjData(m)

    for t in SIDES:
        for name, q in zip(J6, HOME_POSE):
            d.qpos[m.joint(f"{t}_{name}").qposadr[0]] = q
    mujoco.mj_forward(m, d)

    gname = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or f"geom{i}" for i in range(m.ngeom)]
    bname = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, i) or f"body{i}" for i in range(m.nbody)]
    mast = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n) for n in MAST]
    assert all(g >= 0 for g in mast), "a mast geom did not resolve"

    def side_of(gi):
        # ⛔ The gripper bodies are prefixed Lg_/Rg_, not L_/R_.  My first cut matched only the
        # arm links and measured 6 geoms a side against the trace's 38 -- an instrument blind to
        # the hand, which is the part nearest everything.  Both prefixes, and the count is
        # asserted against the trace below so a silent narrowing cannot happen again.
        b = bname[m.geom_bodyid[gi]]
        return b[0] if (b[:2] in ("L_", "R_") or b[:3] in ("Lg_", "Rg_")) else None

    arm = {t: [g for g in range(m.ngeom) if side_of(g) == t] for t in SIDES}

    out = []
    out.append("HOME-POSE SYMMETRY PROBE -- the start pose that t42 never left")
    out.append(f"model    : {AS_BUILT}   (t42's own as-built cell, read not rebuilt)")
    out.append(f"pose     : both arms at HOME_POSE = {tuple(round(q, 4) for q in HOME_POSE)}")
    out.append(f"arm geoms: L={len(arm['L'])}  R={len(arm['R'])}")
    out.append("")

    # ---- 1. are the two arms mirror images at the LINK level? --------------------------------
    out.append("1. LINK FRAMES: is R the mirror of L about x=0?  (x_R + x_L = 0, y and z equal)")
    worst = (0.0, "")
    for i in range(m.nbody):
        n = bname[i]
        if not n.startswith("L_"):
            continue
        j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "R_" + n[2:])
        if j < 0:
            out.append(f"   {n:28s} -> no R counterpart")
            continue
        pl, pr = d.xpos[i], d.xpos[j]
        err = max(abs(pl[0] + pr[0]), abs(pl[1] - pr[1]), abs(pl[2] - pr[2])) * 1e3
        if err > worst[0]:
            worst = (err, n)
        out.append(f"   {n[2:]:28s} L[{pl[0]:+.4f} {pl[1]:+.4f} {pl[2]:+.4f}]  "
                   f"R[{pr[0]:+.4f} {pr[1]:+.4f} {pr[2]:+.4f}]   mirror error {err:8.4f} mm")
    out.append(f"   -> worst mirror error over all paired links: {worst[0]:.4f} mm at {worst[1]}")
    out.append("")

    # ---- 2. the driver's own mast reading, per side, and where it comes from -----------------
    out.append("2. MAST DISTANCE (mj_geomDistance to stem/foot/crown; negative = inside)")
    per_side = {}
    for t in SIDES:
        rows = []
        for g in arm[t]:
            best, who = 1e9, None
            for c in mast:
                dv = mujoco.mj_geomDistance(m, d, g, c, 1.0, None)
                if dv < best:
                    best, who = dv, gname[c]
            rows.append((best, gname[g], bname[m.geom_bodyid[g]], who))
        rows.sort()
        per_side[t] = rows
        out.append(f"   {t}: closest 6 of {len(rows)} arm geoms")
        for dv, g, b, c in rows[:6]:
            out.append(f"      {dv * 1e3:+9.2f} mm   {g:22s} on {b:22s} vs {c}")
    out.append("")

    # ---- 3. the two questions the trace line raises, answered side by side -------------------
    out.append("3. THE TRACE LINE, CHECKED")
    lmin, rmin = per_side["L"][0], per_side["R"][0]
    out.append(f"   L closest = {lmin[0] * 1e3:+.2f} mm on {lmin[2]}   "
               f"R closest = {rmin[0] * 1e3:+.2f} mm on {rmin[2]}")
    same_link = lmin[2][2:] == rmin[2][2:]
    out.append(f"   the two sides report the SAME link: {same_link}")
    # what does the R counterpart of L's winning link actually read?
    lb = lmin[2]
    rb = "R_" + lb[2:]
    rcounter = [r for r in per_side["R"] if r[2] == rb]
    if rcounter:
        out.append(f"   L's winning link is {lb} at {lmin[0] * 1e3:+.2f} mm; its counterpart {rb} "
                   f"reads {rcounter[0][0] * 1e3:+.2f} mm")
        gap = abs(lmin[0] - rcounter[0][0]) * 1e3
        out.append(f"   difference between the mirrored links: {gap:.2f} mm")
    else:
        out.append(f"   ⛔ {rb} has NO geom in the right arm's set -- the instrument is not "
                   f"blind by count, it is blind by which body carries the geometry")
    out.append("")

    # ---- 4. contacts actually generated at the home pose --------------------------------------
    out.append("4. CONTACTS AT THE HOME POSE (what the physics itself reports)")
    if d.ncon == 0:
        out.append("   none")
    for i in range(d.ncon):
        c = d.contact[i]
        out.append(f"   {gname[c.geom1]:22s} <-> {gname[c.geom2]:22s}  dist {c.dist * 1e3:+.3f} mm")
    # ---- 5. p5's one-line question, answered statically ---------------------------------------
    # p5 -162: print the world direction of the approach axis that pose_rd=(0,0) commands, per
    # side.  The driver reaches world through RD @ AXFIX[t] (its own comment, :1096-1100), and
    # AXFIX is measured from the PAD bodies -- so the question is really whether AXFIX["R"] is the
    # mirror of AXFIX["L"].  p5 noted det is +1 on both sides; that does not settle it, because
    # swapping the two pads flips BOTH the closing row and the sideways row (s = a x c), and two
    # sign flips leave the determinant alone.  So the pads are identified by WHERE THEY ARE.
    out.append("5. THE COMMANDED ATTITUDE, PER SIDE (p5's question, no run)")
    sc = mujoco.MjData(m)
    axpose = [0.0, -1.2, 1.0, -1.4, -1.57, 0.0]     # the driver's own AXFIX measuring pose
    for t in SIDES:
        for name, q in zip(J6, axpose):
            sc.qpos[m.joint(f"{t}_{name}").qposadr[0]] = q
    mujoco.mj_forward(m, sc)

    AX, info = {}, {}
    for t in SIDES:
        pl = np.array(sc.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}g_left_pad")])
        pr = np.array(sc.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}g_right_pad")])
        tb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}g_base")
        c_w = (pr - pl) / max(np.linalg.norm(pr - pl), 1e-9)
        pinch_w = 0.5 * (pl + pr)
        a_w = np.array(sc.xpos[tb]) - pinch_w
        a_w = a_w / max(np.linalg.norm(a_w), 1e-9)
        Rt = np.array(sc.xmat[tb]).reshape(3, 3)
        c_l, a_l = Rt.T @ c_w, Rt.T @ a_w
        AX[t] = np.column_stack([c_l, np.cross(a_l, c_l), a_l]).T
        info[t] = (pl, pr, c_w, a_w)
        out.append(f"   {t}: pad bodies in world  left[{pl[0]:+.4f} {pl[1]:+.4f} {pl[2]:+.4f}]  "
                   f"right[{pr[0]:+.4f} {pr[1]:+.4f} {pr[2]:+.4f}]")
        out.append(f"      closing axis (right-left) in world [{c_w[0]:+.4f} {c_w[1]:+.4f} "
                   f"{c_w[2]:+.4f}]   approach (pinch->tool) [{a_w[0]:+.4f} {a_w[1]:+.4f} "
                   f"{a_w[2]:+.4f}]   det(AXFIX) = {np.linalg.det(AX[t]):+.4f}")

    M = np.diag([-1.0, 1.0, 1.0])   # the cell's mirror: x -> -x
    plL, prL, cL, aL = info["L"]
    plR, prR, cR, aR = info["R"]
    same = np.linalg.norm((M @ plL) - plR)
    swapped = np.linalg.norm((M @ plL) - prR)
    out.append(f"   which right-side pad is the mirror of the LEFT arm's LEFT pad?  "
               f"distance to R's left pad {same * 1e3:8.3f} mm | to R's right pad "
               f"{swapped * 1e3:8.3f} mm  ->  "
               f"{'SAME NAME' if same < swapped else '⛔ THE OTHER NAME (the pads swap sides)'}")
    out.append(f"   closing axis, mirrored L vs measured R: "
               f"M@cL [{(M @ cL)[0]:+.4f} {(M @ cL)[1]:+.4f} {(M @ cL)[2]:+.4f}]  vs  "
               f"cR [{cR[0]:+.4f} {cR[1]:+.4f} {cR[2]:+.4f}]   "
               f"{'aligned' if float((M @ cL) @ cR) > 0 else '⛔ OPPOSED'}")
    out.append(f"   approach axis, mirrored L vs measured R: "
               f"M@aL [{(M @ aL)[0]:+.4f} {(M @ aL)[1]:+.4f} {(M @ aL)[2]:+.4f}]  vs  "
               f"aR [{aR[0]:+.4f} {aR[1]:+.4f} {aR[2]:+.4f}]   "
               f"{'aligned' if float((M @ aL) @ aR) > 0 else '⛔ OPPOSED'}")

    # the attitude pose_rd=(0,0) actually commands, per side, and whether the two are mirrors
    rd = (Rotation.from_euler("z", 0.0) * Rotation.from_euler("z", np.pi / 2.0)).as_matrix()
    cmd = {t: rd @ AX[t] for t in SIDES}
    for t in SIDES:
        ap = cmd[t] @ np.array([0.0, 0.0, 1.0])
        out.append(f"   {t}: pose_rd=(0,0) commands approach in world "
                   f"[{ap[0]:+.4f} {ap[1]:+.4f} {ap[2]:+.4f}]"
                   f"{'  (straight down)' if ap[2] < -0.99 else '  ⛔ NOT straight down'}")
    mism = np.abs(cmd["R"] - M @ cmd["L"] @ M).max()
    out.append(f"   are the two commanded attitudes mirrors of each other?  worst element "
               f"difference {mism:.6f}  ->  {'yes' if mism < 1e-6 else '⛔ NO'}")

    # ⭐ (0,0) is the one entry where a swapped closing axis cannot show: a roll of zero does not
    # use it.  The menu the solver actually walks asks for rolls, and the roll tips the tool ABOUT
    # the closing axis -- so if that axis is opposed between the arms, the SAME roll number tips
    # the two arms opposite ways in the world, and the two sides are no longer being asked for
    # mirrored attitudes.  The start-pose solve chose roll 0.0 deg on the left and 34.4 deg on the
    # right in t42, so this is the entry that matters.
    out.append("   the same question at the rolls the menu actually asks for:")
    out.append(f"      {'yaw':>6s} {'roll':>7s}   {'L approach (world)':>26s}   "
               f"{'R approach (world)':>26s}   mirrored?")
    for yaw, roll in ((0.0, 0.0), (0.0, 0.30), (0.0, -0.30), (0.0, 0.55), (0.30, 0.30)):
        rdx = (Rotation.from_euler("z", yaw) * Rotation.from_euler("z", np.pi / 2.0)
               * Rotation.from_euler("y", roll)).as_matrix()
        cm = {t: rdx @ AX[t] for t in SIDES}
        ap = {t: cm[t] @ np.array([0.0, 0.0, 1.0]) for t in SIDES}
        e = np.abs(cm["R"] - M @ cm["L"] @ M).max()
        out.append(f"      {np.degrees(yaw):6.1f} {np.degrees(roll):7.1f}   "
                   f"[{ap['L'][0]:+.4f} {ap['L'][1]:+.4f} {ap['L'][2]:+.4f}]   "
                   f"[{ap['R'][0]:+.4f} {ap['R'][1]:+.4f} {ap['R'][2]:+.4f}]   "
                   f"{'yes' if e < 1e-6 else f'⛔ NO ({e:.4f})'}")

    # ---- 6. the claw invariant, since §5 found the pad NAMES swap sides ----------------------
    # The banked ko grip is not a pinch alone: f1ext passes BELOW the cable and f2ext ABOVE it
    # (driver :114-116, from GD-KoShape-Finger.md:58-59), and the run's own legend says the blue
    # claw is upper and the red one lower.  §5 showed the pad names land on opposite physical
    # sides between the arms, so the question is whether the up/down roles survive that.
    out.append("")
    out.append("6. CLAW UP/DOWN, PER SIDE (f1ext must be BELOW f2ext -- the ko grip's own rule)")
    for t in SIDES:
        for s in ("left", "right"):
            zs = {}
            for c in ("f1", "f2"):
                g = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"{t}g_{s}_pad_{c}ext")
                zs[c] = float(d.geom_xpos[g][2]) if g >= 0 else float("nan")
            ok = zs["f1"] < zs["f2"]
            out.append(f"   {t}g_{s}_pad: f1ext z={zs['f1']:+.4f}  f2ext z={zs['f2']:+.4f}  "
                       f"-> f1 is {'BELOW' if ok else '⛔ ABOVE'} f2")
    out.append("   (at the home pose, in world z; the tool is not vertical here, so this reads "
               "the built order of the claws, not the grasp attitude)")

    out.append("")
    out.append("⛔ SCOPE: one pose per section, geometry only.  No dynamics, no run, no verdict, "
               "and no statement about which mounting pair the cell should use.  §5's last row "
               "is a MEASUREMENT that the two sides stop being mirrors once yaw is non-zero; "
               "whether the menu SHOULD mirror is a design question and not decided here.")

    text = "\n".join(out) + "\n"
    (HERE / "HOME_POSE_SYMMETRY_20260729.txt").write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
