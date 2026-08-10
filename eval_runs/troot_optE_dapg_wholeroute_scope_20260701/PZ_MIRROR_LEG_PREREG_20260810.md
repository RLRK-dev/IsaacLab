# pZ — pre-registered mirror-predicate leg, written **before p0's announce**

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-08-10 09:1x JST on m-p18-273's heads-up. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Object (when it exists)**: p0's mirror commit, judged **against its own parent**, rows below. The rows bind to observables, so p0's authoring choices (how the mirrored asset is produced) stay free.

## 0. The mechanism, verified from this lane before pre-registering

- Driver `:306` (region `:302-:311`): one `GRIP_XML` loaded for **both** sides, attached under the same fixed rotation — the right hand is the same spec at a rotated frame. `GRIP_XML` = `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml` (driver `:38`).
- `kinonly_step_solve.py:301-:310`: the **same** single-XML mechanism — so the mirror predicate is measurable at this desk through `K.build_cell()`, read-only, as in my other legs.
- `ur15_mirror_meshes/` = exactly **7 files, all arm meshes** (base/forearm/shoulder/upperarm/wrist1/2/3); `find` for any `*mirror*` gripper asset repo-wide: none. No mirrored gripper asset exists.
- `ur15-dual-arm-cell.md:68-70` read with my own eyes: "Joint values are for the left arm; **the right arm is the exact kinematic mirror**."

## 1. The rows

| # | row | requirement |
|---|---|---|
| 1 | asset mechanism | on the announced surfaces, the single-XML-both-sides mechanism is gone: the right attach loads a **distinct mirrored gripper asset/spec**; the left stays the authoritative ko asset (`_ur15_2f85_koshape_actuated.xml`, section-0 #4) |
| 2 | structure vs the provided spec | the landed right-gripper subtree satisfies the mirror relation **measured from the provided URDF itself** (`~/Downloads/ur15-dual-arm-cell/ur15-dual-arm-cell.urdf`, subtree `right_gripper_base` → `right_right_pad` vs the left counterpart, extracted by a **tree walk**, never by name-substring — see §2(d)); pair-by-pair on joint origins, axes, and link frames |
| 3 | mesh chirality — the decisive row | paired gripper meshes (**paired via bodies**; the gripper geoms are unnamed) satisfy `V_R == mirror(V_L)` as point sets. Today `V_R == V_L` byte-wise (same source XML) — a reflection of a chiral part can never equal its rotation, and the ko claw is chiral. Banked ruling `P4_RS_RULING_20260727_ROBOT_UR15.md:67-69` (**a sign flip does not make a mirror**) is this row's own warning: §2(a) shows the transform level is one sign away from passing, so meshes, not signs, decide |
| 4 | world composition | at a configuration the **provided spec designates as mirrored** (md Poses: left values, right = exact kinematic mirror; or a mirror-check pose the landing itself designates), paired gripper geom world clouds satisfy `{x_R} == {diag(−1,1,1)·x_L}`. ⚠ anchored to the spec's designation only — never to my own frame (§2(b) is why) |
| 5 | no behavior change elsewhere | the wired servo lineage stays as landed; STEP2 L-stall surfaces untouched (independent, per the word); announce-first; function-named pins |
| 6 | no run | ⛔ the one-run authorization was consumed at STEP 2 — this leg is fully static (`mj_kinematics`-class only), and no re-run happens from this desk under any row |
| 7 | judgment | parent-relative on the announced commit; every row's evidence carries `file:line` / blob sha; kinonly's nominated blob `120746a49b` is immutable regardless (its own re-nomination, if the fix touches the instrument, is a separate later act) |

## 2. Today's controls — the firing side, and three dead queries recorded so nobody inherits them

- **(a) transform level, measured** (via `K.build_cell`, body pairs by name, 14 found): internal parent-relative transforms **identical 14/14** (the rotated-copy signature) — yet mirror conjugation (`pos → diag(−1,1,1)·pos`, `quat (w,x,y,z) → (w,x,−y,−z)`) coincidentally already holds for **13/14** (x-mirror-invariant shapes). The discriminating pair is **`base`**: `quat = rot_z(−90°)` both sides where a mirror needs `+90°`. One sign — which is exactly why row 3, not signs, must decide.
- **(b) dead query 1**: equal-q world reflection is NOT a mirror test — the design's `HOME_POSE` is one 6-tuple for both arms (spec `:455`; the bank's `path_from_L == path_from_R`), and arm frames do not world-mirror at equal q (measured: wrist-3 reflected mismatch ~1.75 m). Any row anchored to "reflect at equal q" measures my frame, not the cell.
- **(c) dead query 2**: axis-direction-only mirror signs (`S = [+1×6]` measured) are necessary, not sufficient — directions mirrored while positions did not. S-mirrored q does not produce mirrored frames here.
- **(d) dead query 3**: name-substring filters missed three times tonight — gripper geoms are **unnamed** (name-pairing returns the empty set and a dead 0/0/0), and URDF finger joints do not contain "grip" (`left_left_driver…`, `right_right_pad`). Pair via **bodies** in MJCF and via **tree walk** in URDF.
- **(e) asset level**: one file, both sides, measured at driver `:306` and kinonly `:301-:310`; no mirrored gripper asset exists on disk (§0).

## 3. Provenance

Reads: `git`-tracked driver/instrument blobs and the provided `~/Downloads/ur15-dual-arm-cell/` spec; measurements via read-only `K.build_cell()` + `mj_kinematics` (step count 0 by construction). Zero tracked-content modifications by pZ. **Written, not banked; banking requested of a custodian.**
