# pZ — verdict on the right-hand mirror, `b7a5e39ecf`, judged by the banked mirror rows

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-08-10 09:1x–09:2x JST. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Rows** = `PZ_MIRROR_LEG_PREREG_20260810.md` @ `9d118cbf93` (sha `3e7cef105a…`), banked **before the mirror existed**.
**Judged against the commit's own parent** `453829041d`.
⚠ **Announce status**: p0's announce had not reached my desk when I measured (m-p18-276 asked for it at 09:10; I read the landed object at 09:09–09:20). The object is immutable in git, so every measurement below stands regardless of the announce's wording; if the announce names a different object, this verdict names the wrong one and I re-run.

## 0. Object

`b7a5e39ecf` (09:09:05, "Mirror the right hand: baked ko asset, measured local mirror"), 12 files: the mirrored gripper XML, 8 baked STLs in `ko_mirror_meshes/`, the generator `make_ko_mirror.py`, the acceptance `ur15_gripper_mirror_acceptance.py`, and the driver at **+9/−1**.

## 1. The rows

| # | row | verdict | evidence measured by me |
|---|---|---|---|
| 1 | asset mechanism | **holds** | driver `:307`: `mujoco.MjSpec.from_file(GRIP_XML if tag == "L" else GRIP_XML_MIRRORED)`; parent `453829041d` contains `GRIP_XML_MIRRORED` **0×**, the commit **2×**; left stays the authoritative ko asset (`_ur15_2f85_koshape_actuated.xml`, section-0 #4) |
| 2 | mirror relation vs the provided spec | **holds — but not through the instrument I registered** (§2) | the provided URDF's gripper subtree is **not itself mirrored**; the operative mirror is `A = Rtᵀ R_Rᵀ M R_L Rt`, which I computed independently as **exactly `diag(−1,1,1)`**, det −1, signed permutation, unchanged at tilt 20°/45°/0°; wrong-plane controls (y, z) do **not** produce it |
| 3 | mesh chirality — **decisive** | **holds, exact** | my own file-level read of all 8 STL pairs: symmetric Hausdorff(A·V_L, V_R) = **0.000e+00** on every mesh, 191,118 verts / 63,706 triangles; identity control = **5.86 m** (fires); winding preserved (stored vs geometric normal agreement 1.00 both sides) |
| 4 | world composition | **holds, reproduced + audited** | p0's acceptance re-run by me in an isolated copy: TEST **192/192**, worst Hausdorff 4.1e−5 mm; NEGATIVE (left asset on the right) **0/192**, worst 135.4 mm — the must-fail leg fires; my audit of their instrument in §3 |
| 5 | no behavior change elsewhere | **holds** | driver diff +9/−1, entirely one branch line plus comment inside the attach region; lines touching `set_joint|ctrl|qpos|mj_step|SETTLE` = **0**; all 12 files are inside the mirror scope; STEP2 L-stall surfaces untouched |
| 6 | no run | **holds** | every measurement is file-level, XML-level, or `mj_kinematics`-only; the acceptance is kinematics-only by its own code (read, not assumed); nothing wired ran; no run authorization sought or used |
| 7 | parent-relative judgment | **holds** | parent `453829041d`; every row above measured as a difference from it |

## 2. ⚠ Row 2's registered instrument was vacuous — measured, not assumed

m-p18-273 §2 named the mirror relation as the provided URDF's `right_gripper_base` → `right_right_pad` subtree (md `:70` "exact kinematic mirror"), and my prereg bound row 2 to it. Measured at this desk by tree walk (11 links per side):

- **all 11 gripper joint origins have x = 0** ⇒ the mirror rule is a **no-op** on every one; **0 of 11 pairs discriminate**;
- left and right links reference the **same mesh files** (`robotiq_arg2f_85_*.dae`, `robotiq_gripper_coupling.stl`);
- the only differing rpy anywhere in that region is the **arm's** base mount (±0.7854 rad = the yoke tilt), not a gripper link.

⇒ The provided URDF carries the **naming and the tree**, not a mirrored gripper asset — and it is a Robotiq 2F-85 reference, not the ko claw. A leg that had leaned on it would have "passed" 11/11 while measuring nothing. The mirror content had to come from elsewhere, and p0 took it from the built mounts; I verified that operator independently (§1 row 2). **The row's intent is satisfied by a stronger source than the one I named**, and I record the vacuity so nobody re-uses my instrument thinking it discriminates.

## 3. Audit of p0's acceptance (so my row 4 is not correlated assent)

Reproduced in an isolated copy (`cp -r`, never overwriting their `_gen/`): rc 0, VERDICT PASS. What I checked about the instrument rather than taking its output:

- **Comparator**: symmetric Hausdorff via KD-trees on **world point sets** — no ordering, no frame. Their docstring records why: MuJoCo re-frames every mesh by principal axes at load, so post-load frames differ by convention across a reflection (their measurement: 38 nm position vs 2.0 frame error). ⭐ This also **corrects my own prereg**, which had planned a lexicographic sorted-set comparator — the exact form they measured wrong.
- **Denominator**: published as 192 and **re-derived by me**: I counted the compared geoms myself = **32** (24 mesh + 8 box) × 2 arm poses × 3 finger states = 192.
- **The degenerate branch**: `shape_points` returns a single centre point for geoms that are neither mesh nor box — which would silently reduce those rows to a position check. Measured: **0 of 32** geoms take that branch here, so the weakening is vacuous **on this object** (it would matter if a capsule/sphere were added later).
- **Negative leg**: fires — 0/192 at 135.4 mm, i.e. the filmed defect is exactly what the test rejects.
- **Stand-in fidelity**: their constants equal the driver's — TILT 1.22173, YOKE_SPREAD 0.28, SHOULDER_HEIGHT 1.53, `R_TOOL` matrix == the driver's `Rt` product (checked numerically), `SIDE_SIGN == spec:485 SIDES = {"L": −1.0, "R": +1.0}`.
- **Boundary named**: the acceptance builds a **stand-in** (column + one arm + one gripper), not the driver's full cell. The driver's own composition is verified here only at source level (row 1's branch). Whole-cell composition remains unmeasured by both desks — it is not measurable at this desk without importing the driver, which is forbidden.
- **Coverage complement**: their file-level vertex check covers **1 of 8** meshes (spring_link); mine covers **8 of 8** independently.

## 4. Honest scope of row 3

Three of the eight meshes (`driver`, `pad`, `silicone_pad`) are **x-symmetric**: their identity control reads exactly 0, so for those the mirror row is trivially true and proves nothing. The row **discriminates on 5 of 8** — `base_mount` 6.36 m, `base` 2.79 m, `coupler` 0.26 m, `follower` 0.44 m, `spring_link` 0.18 m of identity-distance. The chirality that Rs1 (the human) saw lives in those five.

## 5. What this verdict does NOT establish

Whether the filmed configuration now looks right to Rs1 — visual physical validity is Rs1's court alone (role brief `:28`), and no video exists of the post-mirror head. Whether the arms as a pair mirror in the driver's built cell (§3's boundary). Anything about the reshoot, which stays behind Rs1's authorization; dep-2 remains the grade cap; DEV-C2X's 35 mm stays unruled.

## 6. Provenance

`git show`/`numstat`/blob-id equality; `sha256sum`; own STL binary reader + `scipy.spatial.cKDTree`; own XML tree walk; own computation of `A` from the spec's mount frames; one isolated reproduction of p0's acceptance. Zero tracked-content modifications by pZ. **Written, not banked; banking requested of a custodian.**
