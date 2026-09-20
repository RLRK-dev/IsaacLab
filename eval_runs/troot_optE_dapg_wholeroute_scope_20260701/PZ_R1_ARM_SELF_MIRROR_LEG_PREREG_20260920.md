# pZ — pre-registered leg R1 (arm self-mirror on the composed arm-only models; v3 §10 R1 @ `8d9fdf3bbb` `:138`, §17.3 pin @ `e6172b2e3b`; p4's adopted order `caa742b8d3` via m-p4-288), written before the instrument has been run

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 14:24:38 JST on m-p18-426 (p4 m-p4-288 (2): 「R1（HOME_POSE・乱数 M ≥ 24・不動点除外・seed 事前登録・R 式の負の対照・build_side の composed model 上）」; the row itself names `ur15_mirror_acceptance.py::build()` = the arm-only builder, which this leg uses — p4's 「build_side」 is the hand-on-arm builder of R1′). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. **Landed ≠ accepted**.

**Order of existence (measured in the writing command)**: the instrument's outputs `r1.json` / `r1.log` do **not** exist (asserted); commits touching `ur15_mirror_acceptance.py` after `92059373a3` = **0**; HEAD `2a04895e54`. The seed, the draw count, the exclusion radius and every bar below are fixed here **before** any draw is made.

**Objects (blobs at HEAD; the leg runs in the `git archive` of `92059373a3`, whose blobs for these files are the same — verified in `PZ_VERDICT_R1P_HAND_ON_ARM_LEG_20260920.md`)**: `ur15_mirror_acceptance.py` `11ea985d8b19` (its `build()` `:62-73` and `tool_pose()` are AST-identical to the parent blob `0803ea391298`'s — window W changed only `REF_DIR` and `main()`, predicate v2); `ur15_base.xml` `7334710cc0d6`; `ur15_base_mirrored.xml` `6751866fd3f4`; `ur15_cell_spec.py` `6bdf7ea4f9ca` (`LIMS = tuple((lo, hi) for _, lo, hi in _arm_limits_from_urdf…` `:100`; `HOME_POSE = (-3.1521, -0.2867, 2.4674, -1.3953, 1.5634, -1.5782)` `:455`); reference JSON `6db65e349131` sha256 `20ac0935c707757c35a974f4c7adc9b9412ed18a04905f06b34dc76affa3990d` (§17.3: the repo copy is the pin; read by this desk's own loader, the acceptance script's `REF_DIR` not used). **Mount** = `ur15_cell_spec` live import with no overrides = the C-2 defaults (YOKE_SPREAD 0.28, TILT 70°, SHOULDER_HEIGHT 1.53) — p11 `:138` 「mount 不変・C-2 既定」; the identity/mirror predicates are mount-independent by construction (both sides get the same mount magnitude with opposite sign), so no override is set.

## Rows (bars from v3 §10 R1 `:138`: position ≤ 1e-3 mm, rotation ≤ 1e-6 rad; negative control ≥ 10 mm — this court's grade)

| # | row | requirement (fixed now) |
|---|---|---|
| R1-1 | identity joint map at **HOME_POSE** | on the mirrored arm (right mount, sign +1) with **the same q** as the stock arm (left mount, sign −1): for each of the 6 link bodies `a_shoulder_link … a_wrist_3_link`, `|Mx·p_L − p_R| ≤ 1e-3 mm` and `‖rotvec(R_Rᵀ·Mx·R_L·Mx)‖ ≤ 1e-6 rad` (`Mx = diag(−1,1,1)`) |
| R1-2 | the reference's **24 left on-yoke poses** (`poses[*].left.joints_on_yoke_rad`, JSON sha256 `20ac0935c707757c…`) | same bars, all 24 × 6 bodies. (Note: the JSON's right column is exactly the R-form of its left column — 08-10 B1 — so it is the negative control's input, not the identity map's) |
| R1-3 | **random in-limit draws**: `M = 24`, `seed = 20260920` (`numpy.random.default_rng`), each joint uniform in `LIMS` (`ur15_cell_spec:100`, the URDF limits), **excluding** draws within `RADIUS = 0.1` rad (wrap-aware Chebyshev distance) of the R-form fixed point `q* = (0, π/2, 0, π/2, 0, 0)`; the number of rejected draws is reported | same bars, all 24 × 6 bodies |
| R1-4 | **negative control (i) = the R-form** `q_R = (−q0, π−q1, −q2, π−q3, −q4, −q5)` (the reference's right-column rule, v3 `:24`; = the non-mirrored machine's path, expected to FAIL on UR15-B) on the mirrored arm, for every pose of every set | `|Mx·p_L(q) − p_R(R-form(q))|` at `a_wrist_3_link` **≥ 10 mm on every pose**. p11's CC4-derived expectation (their own draws): HOME 664.70 mm, reference-24 min 357.68 mm, random-24 min 51.3 mm — the first two are reproducible here (same inputs), the third is not (their seed is not published); this desk's random minimum is whatever the 24 pre-registered draws give, banked as measured |
| R1-5 | **negative control (ii) = the stock arm on the right mount** (`build("ur15_base.xml", +1)`, the rotated-copy arm), identity q | wrist_3 margin ≥ 10 mm on every pose of every set |
| R1-6 | **the fixed point itself** under control (i) | `q* = (0, π/2, 0, π/2, 0, 0)`, `R-form(q*) = q*` (mod 2π): the negative control's margin at `q*` must read **≈ 0** (≤ 1e-6 mm) — the reason the exclusion exists; if it did not read 0 the exclusion would be a rule without a cause |
| R1-7 | control invariance / no run | `mj_step` calls = 0 (counted); driver family in `sys.modules` = []; `mj_kinematics` only; run 0 |
| R1-8 | pins | the blobs above; instrument sha; env7 python 3.12.3 / mujoco 3.11.0 |

**Not a row (stated so it is not read as one)**: the **tool0 rotation** is not of the `Mx·R·Mx` form because `R_TOOL` is applied identically on both sides (`tool_pose` `:81-82`: `R_tool0 = R_wrist3 · R_TOOL`), which is exactly why the hand's relation carries the `A` factor (R1′ row b1); tool0's **position** equals `a_wrist_3_link`'s (the offset is a pure rotation at the wrist origin), so it is covered by R1-1..3. Hand bodies are R1′'s; joint limits / masses / inertias are R2's; motion is #69's.

**Falsification forms**: any identity pose above a bar ⇒ the arm asset (or its mount) is not the mirror ⇒ back to the asset court (p11 `:149`'s form), not a controller finding; a negative-control margin below 10 mm on an included pose ⇒ reported as such (the radius is not adjusted after the fact); the fixed-point margin not ≈ 0 ⇒ the R-form or the fixed point is mis-stated in this pre-registration ⇒ reported.

## Leg procedure
`3.12.3 3.11.0` on the archive: `python pz_r1.py <archive sim dir> r1.json 20260920 24 0.1` once; the verdict artifact embeds the log verbatim and judges each row against the bars above; nothing is re-drawn.

## Appendix A — `pz_r1.py` (verbatim; sha256 b52621fa0927cc8ebb9ea89b45793c1bac0b5ca548c05c36412ddda7a5d9b033)
```python
"""pZ R1 instrument (v3 section 10 R1, arm self-mirror on the composed arm-only models of ur15_mirror_acceptance.build()):
identity joint map q_R = q_L on {HOME_POSE, the reference's 24 left on-yoke poses, M in-limit random draws (seed pre-registered; draws within
RADIUS of the R-form fixed point q* = (0, pi/2, 0, pi/2, 0, 0) excluded, wrap-aware)}; predicates per arm link body: |Mx.p_L - p_R| and
||rotvec(R_R^T . Mx . R_L . Mx)||.  Negative controls: (i) q_R = Rform(q_L) = (-q0, pi-q1, -q2, pi-q3, -q4, -q5) on the mirrored arm;
(ii) the stock arm on the right mount (RC) with the identity map; (iii) the fixed point itself under (i) (must read ~0: why the exclusion exists).
argv: W(archive sim dir) OUT.json SEED M RADIUS.  Static: mj_kinematics only; mj_step counted (must stay 0)."""
import sys, io, json, math, contextlib, hashlib, numpy as np, mujoco
from scipy.spatial.transform import Rotation
W, OUT, SEED, M, RADIUS = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
sys.path.insert(0, W)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    import ur15_mirror_acceptance as acc; import ur15_cell_spec as spec
steps = 0; _orig = mujoco.mj_step
def _counted(*a, **k):
    global steps; steps += 1; return _orig(*a, **k)
mujoco.mj_step = _counted
Mx = np.diag([-1.0, 1.0, 1.0]); LINKS = ["a_shoulder_link", "a_upper_arm_link", "a_forearm_link", "a_wrist_1_link", "a_wrist_2_link", "a_wrist_3_link"]
with contextlib.redirect_stderr(io.StringIO()):
    mL, dL = acc.build("ur15_base.xml", acc.SIDE_SIGN["L"]); mR, dR = acc.build("ur15_base_mirrored.xml", acc.SIDE_SIGN["R"]); mC, dC = acc.build("ur15_base.xml", acc.SIDE_SIGN["R"])
def place(m, d, q):
    for name, v in zip(acc.J6, q): d.qpos[m.joint(f"a_{name}").qposadr[0]] = v
    mujoco.mj_kinematics(m, d)
def frames(m, d): return {n: (np.array(d.xpos[m.body(n).id]), np.array(d.xmat[m.body(n).id]).reshape(3, 3)) for n in LINKS}
def rform(q): return [-q[0], math.pi - q[1], -q[2], math.pi - q[3], -q[4], -q[5]]
QSTAR = [0.0, math.pi / 2, 0.0, math.pi / 2, 0.0, 0.0]
def wrapdist(q): return max(abs((a - b + math.pi) % (2 * math.pi) - math.pi) for a, b in zip(q, QSTAR))   # wrap-aware Chebyshev distance to the fixed point
ref = json.loads(open(f"{W}/reference/ur15-dual-arm-cell/ur15-dual-arm-cell.json").read()); REF_SHA = hashlib.sha256(open(f"{W}/reference/ur15-dual-arm-cell/ur15-dual-arm-cell.json", "rb").read()).hexdigest()
LIMS = [tuple(map(float, l)) for l in spec.LIMS]; assert len(LIMS) == 6
rng = np.random.default_rng(SEED); draws, rejected = [], 0
while len(draws) < M:
    q = [float(rng.uniform(lo, hi)) for lo, hi in LIMS]
    if wrapdist(q) < RADIUS: rejected += 1; continue
    draws.append(q)
sets = {"HOME_POSE": [("HOME_POSE", list(map(float, spec.HOME_POSE)))],
        "reference_24_left_on_yoke": [(name, [float(v) for v in p["left"]["joints_on_yoke_rad"]]) for name, p in ref["poses"].items()],
        f"random_{M}_seed_{SEED}": [(f"draw{i}", q) for i, q in enumerate(draws)]}
def eval_set(rows):
    out = {"n": len(rows), "identity": {"max_pos_mm": 0.0, "max_rot_rad": 0.0, "worst_pos_at": None, "worst_rot_at": None},
           "neg_Rform": {"min_wrist3_mm": 1e9, "min_at": None, "max_over_links_min_mm": 1e9}, "neg_RC_identity": {"min_wrist3_mm": 1e9, "min_at": None}, "per_pose": []}
    for name, q in rows:
        place(mL, dL, q); place(mR, dR, q); place(mC, dC, q); fL, fR, fC = frames(mL, dL), frames(mR, dR), frames(mC, dC)
        pe = {n: float(np.linalg.norm(Mx @ fL[n][0] - fR[n][0])) * 1000 for n in LINKS}
        re_ = {n: float(np.linalg.norm(Rotation.from_matrix(fR[n][1].T @ Mx @ fL[n][1] @ Mx).as_rotvec())) for n in LINKS}
        pc = {n: float(np.linalg.norm(Mx @ fL[n][0] - fC[n][0])) * 1000 for n in LINKS}
        place(mR, dR, rform(q)); fRn = frames(mR, dR)
        pn = {n: float(np.linalg.norm(Mx @ fL[n][0] - fRn[n][0])) * 1000 for n in LINKS}
        rec = {"name": name, "q": q, "dist_to_fixed_point_rad": wrapdist(q), "identity_max_pos_mm": max(pe.values()), "identity_max_rot_rad": max(re_.values()),
               "neg_Rform_wrist3_mm": pn["a_wrist_3_link"], "neg_Rform_max_link_mm": max(pn.values()), "neg_RC_wrist3_mm": pc["a_wrist_3_link"]}
        out["per_pose"].append(rec)
        I = out["identity"]
        if rec["identity_max_pos_mm"] > I["max_pos_mm"]: I["max_pos_mm"], I["worst_pos_at"] = rec["identity_max_pos_mm"], name
        if rec["identity_max_rot_rad"] > I["max_rot_rad"]: I["max_rot_rad"], I["worst_rot_at"] = rec["identity_max_rot_rad"], name
        N = out["neg_Rform"]
        if rec["neg_Rform_wrist3_mm"] < N["min_wrist3_mm"]: N["min_wrist3_mm"], N["min_at"] = rec["neg_Rform_wrist3_mm"], name
        N["max_over_links_min_mm"] = min(N["max_over_links_min_mm"], rec["neg_Rform_max_link_mm"])
        C = out["neg_RC_identity"]
        if rec["neg_RC_wrist3_mm"] < C["min_wrist3_mm"]: C["min_wrist3_mm"], C["min_at"] = rec["neg_RC_wrist3_mm"], name
    return out
res = {"seed": SEED, "M": M, "radius_rad": RADIUS, "rejected_draws": rejected, "LIMS": LIMS, "HOME_POSE": list(map(float, spec.HOME_POSE)), "ref_json_sha256": REF_SHA,
       "mount": {"YOKE_SPREAD": float(acc.YOKE_SPREAD), "TILT_rad": float(acc.TILT), "SHOULDER_HEIGHT": float(acc.SHOULDER_HEIGHT)}, "links": LINKS, "sets": {k: eval_set(v) for k, v in sets.items()}}
# (iii) the fixed point itself under the R-form: the negative control's margin there (expected ~0 -- the reason for the exclusion)
place(mL, dL, QSTAR); place(mR, dR, rform(QSTAR)); fL, fRn = frames(mL, dL), frames(mR, dR)
res["fixed_point_check"] = {"q_star": QSTAR, "Rform_q_star": rform(QSTAR), "neg_Rform_wrist3_mm_at_q_star": float(np.linalg.norm(Mx @ fL["a_wrist_3_link"][0] - fRn["a_wrist_3_link"][0])) * 1000}
res["mj_step_calls"] = steps; res["driver_family_in_sys_modules"] = [k for k in sys.modules if "ur15_steps" in k]
open(OUT, "w").write(json.dumps(res, indent=1))
print(f"[r1] mount {res['mount']} | LIMS {LIMS} | seed {SEED} M {M} radius {RADIUS} rejected {rejected} | ref json sha256 {REF_SHA[:16]}")
for k, v in res["sets"].items():
    print(f"[r1] set {k:28s} n={v['n']:2d}: identity max pos {v['identity']['max_pos_mm']:.3e} mm (at {v['identity']['worst_pos_at']}), max rot {v['identity']['max_rot_rad']:.3e} rad (at {v['identity']['worst_rot_at']}) | "
          f"neg R-form: min wrist_3 {v['neg_Rform']['min_wrist3_mm']:.3f} mm (at {v['neg_Rform']['min_at']}), min over poses of max-link {v['neg_Rform']['max_over_links_min_mm']:.3f} mm | neg RC identity: min wrist_3 {v['neg_RC_identity']['min_wrist3_mm']:.3f} mm (at {v['neg_RC_identity']['min_at']})")
print(f"[r1] fixed point q*={QSTAR}: R-form(q*)={res['fixed_point_check']['Rform_q_star']} -> negative-control margin at q* = {res['fixed_point_check']['neg_Rform_wrist3_mm_at_q_star']:.3e} mm")
print(f"[r1] mj_step calls: {steps}; driver family in sys.modules: {res['driver_family_in_sys_modules']}")
```

## Provenance
Blob ids by `git ls-tree` at HEAD; `build()` identity between the parent and landed acceptance blobs by `diff`; no instrument output exists at writing (asserted in the writing command). Committed by pZ under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction m-p18-426.
