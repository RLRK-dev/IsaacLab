---
doc_class: reference
---

# FIX-⑤ /geometric-design output — X-follow re-center of x_grasp (forced gate)

Position-derivation change: re-center `x_grasp` on the measured settled cable X (X analog of caveat-a Y) in `_run_mujoco_grasp_route`, **offset-gated (dx≠0 only)**. Charter `charter_b2_fix5_xfollow_coord.txt` (Rs ⑤=A GO). **2026-07-03.** 0-commit.

## Step 0 — Interrogate the mechanism (bounded, one pass)
- **Necessary?** YES. CP-A (`b2_cpA_reach_screen_finding.md`, commit 5cdcf511c9) proved the canonical route has ZERO cable-X follow (`x_grasp=GRASP_X` const :3564) → any dx≠0 demo is ungraspable (|Δx|>9mm). Without the fix the ±20mm XY DR's X dimension = 0 valid demos.
- **Cheaper salvage?** Opt-2 (Y-only DR, zero code) was surfaced; **Rs adjudicated Opt-1** (X-follow). Not a self-swap.
- **Reuse?** YES — reuses the EXACT caveat-a pattern (same post-settle read, same grasp-region mask), axis 0 instead of 1. Minimal additive, no new mechanism.
- **Downstream risk?** The re-center also shifts the route START (`xk=x_grasp+(x_clip-x_grasp)…` :3952) to the true cable X → CORRECT (drag from where the cable is to the fixed clip). PASS.

## Step 1 — Measured geometry (from code, this session)
| item | value | source |
|---|---|---|
| nominal claw X (`GRASP_X`) | 300 mm | `task_config.py:231` |
| cable diameter Ø | 8.0 mm (radius 4.0) | `test:3590` `CABLE_DIAM_MM=2·CABLE_RADIUS·1e3` |
| claw X-footprint half-extent (`LATERAL_MAX_MM`) | 9.0 mm | `test:3593` (pad-local half_y 0.009; GD-KoShape-Finger.md:51-54) |
| コ mouth inner gap (`MOUTH_MM`) | 10.0 mm | `test:3591` |
| grasp-region mask (Y) | \|Y − grasp_at\| < 100 mm | `test:3865` (grasp_at=`S6_ENGAGE_YC`=0) |
| cable axis | Y (`direction=(0,1,0)`) | `test:1369` → region X ≈ const → mean well-defined |
| grasp X-capture predicate | \|cable_x − claw_x\| < `LATERAL_MAX_MM` (9 mm) | `test:3589` retention/footprint |

## Step 2 — Constraints
**Hard (inviolable):**
- H1 grasp capture: `|cable_x − x_grasp| < 9mm` (else cable outside claw footprint → miss).
- H2 byte-identity: dx=0 / (0,dy) / None MUST keep `x_grasp=GRASP_X` const (proven canonical trajectory). Enforced by the **dx≠0 fire condition** (scene_info :1668 collapses None/(0,0)→(0,0)).
- H3 INVARIANT#2: 88mm span (`GRASP_YC±GHS`) untouched — this change moves X only, span is Y. ✓ (bases fixed, DiffIK unchanged.)
- H4 no kinematic trick: `x_grasp` is a DiffIK EE-X target (via `tgt`→`ik_move_both`), not a teleport. ✓

**Soft:** S1 center the cable in the footprint (maximizes lateral retention margin) — the follow achieves ~0 offset = better than the nominal edge-of-footprint at dx≠0.

**Design space:** with follow, `|Δx|` = settle-ε (sub-mm to ~2mm) vs the 9mm bound ⇒ **≥7mm margin** = 十分 (≥20mm criterion is on Z-design; here the relevant margin is 9mm and follow drives Δ→0).

## Step 3 — Cross-section (X-axis, claw footprint vs cable center; cable ∥ Y = into page)
```
 X [mm]:   291        300        309        320
           |----------claw footprint----------|      (footprint = x_grasp ± 9)
WITHOUT follow (claw fixed @ 300):
  dx=  0   cable●@300   |Δ|=0    INSIDE  (9.0mm margin)   ✅ capture
  dx= +8   ....cable●@308 |Δ|=8  INSIDE  (1.0mm margin)   ⚠✅ marginal
  dx=+10   .....cable●@310 |Δ|=10 OUTSIDE (−1.0mm)        ❌ MISS
  dx=+20   ...........cable●@320 |Δ|=20 OUTSIDE (−11.0mm) ❌ MISS
WITH follow (claw re-centered on measured cable X ≈ 300+dx):
  dx= any  claw & cable co-located, |Δ|=settle-ε (<~2mm) INSIDE (≥7mm margin) ✅ capture
```

## Step 4 — Trade table (H1 capture predicate; H❌ rows excluded from the feasible set)
| dx (mm) | no-follow \|Δx\| | no-follow capture | with-follow \|Δx\| | with-follow capture |
|---|---|---|---|---|
| 0 | 0 | ✅ (byte-identical path — fire cond OFF) | — (OFF, dx=0) | ✅ (unchanged) |
| ±8 (held-out) | 8 | ⚠ 1mm margin | ε≈0 | ✅ |
| ±10 | 10 | ❌ miss | ε≈0 | ✅ |
| ±20 | 20 | ❌ miss | ε≈0 | ✅ |
**Recommendation:** WITH-follow (offset-gated). Restores capture for ALL dx while leaving dx=0/None byte-identical.

## Step 5 — Reality check
1. **Real robot:** re-centering the EE-X command on the perceived cable X is exactly what a real dual-arm grasp does (perceive → position → close). Physically faithful.
2. **Boundary:** settle-ε ±3mm → |Δ|=3 < 9 → capture holds (Step 5a). span/Z untouched.
3. **Dependent params (Step 5b):** `x_grasp` → `tgt(x_grasp,·)` (hover :3881 / descend :3888 / lift :3919) + route start `xk` :3952 + sample :3943 + echo `x_grasp` :5902 (reports followed value). Stale (accepted): camera `_mx` :3715 (record_video only, pre-settle) → framing ≤ dx/2 = 10mm@dx=20 = harmless.
4. **Reverse check:** with follow, claw X = cable X ⇒ cross-section co-located ⇒ H1 satisfied for all dx.

### Step 5a — Settle-ε sensitivity
| factor | range | effect on |Δx| | H1 (9mm) |
|---|---|---|---|
| per-body settle X noise | avg'd over grasp-region mask (many bodies, Y-cable → X≈const) | mean residual sub-mm | ✅ |
| measure→grasp drift (hover/descend steps) | a few physics steps | ~1-2mm | ✅ (≥7mm margin) |
| worst assumed settle-ε | ±3mm | |Δ|=3 | ✅ |
Margin robust; follow drives the systematic dx term to 0, leaving only sub-9mm noise.

### Step 5c — Causal chain (offset → settle → measure → re-center → grasp), 5 steps
| Step | State | Event | Physical response | Outcome | Issue |
|---|---|---|---|---|---|
| 0 | cable@(300+dx, y+dy) | build_scene offset | cable at offset | - | - |
| 1 | settling | 10 physics steps :3854 | cable rests ~(300+dx) | - | - |
| 2 | post-settle | measure X mean over mask | `x_grasp ← 300+dx` | - | - |
| 3 | x_grasp=cableX | `tgt(x_grasp)` hover/descend | claw over cable | - | - |
| 4 | claw@cableX | close | \|Δx\|≈ε<9mm → **capture** | grasp SUCCESS | ✅ |
| 5 | grasped | lift 12-substep | cable caged, rises | HOLD | ✅ |
Contrast (no-follow bug): step 4' claw@300 vs cable@300+dx → |Δ|=dx>9 → empty close → **MISS** ❌. No irreversible state introduced (a bad measure fails gracefully as an ordinary grasp miss). Works regardless of DISABLE_CONTACTS (positioning, not contact-gating).

### Step 5d — Axis-resolved retention
Unchanged. This change POSITIONS the claw; it does not alter the コ two-claw cage (f1ext bottom + f2ext top vertical form-closure + lateral footprint, GD-KoShape-Finger). Retention DOF resolution is inherited. Side benefit: centering the cable in the footprint (vs the nominal edge at dx≠0) IMPROVES the lateral-retention margin.

## Step 6 — Change (the ONLY edit; additive, dx≠0-gated)
Insert after the caveat-a block (`test:3868`), before `def tgt` (`test:3870`):
```python
# fix-⑤ (Rs A 2026-07-03): X analog of caveat-a — re-centre x_grasp on the SETTLED cable X, offset-gated
# (dx != 0 only; scene_info :1668 collapses None/(0,0) -> (0,0) so None / (0,dy) / nominal keep the constant-X
# banked trajectory = byte-identical BY CONSTRUCTION). Cable ∥ Y -> region X ≈ const -> mean well-defined.
# Fixes b2_cpA_reach_screen_finding.md (canonical route had ZERO cable-X follow; do_p1_grasp grasp_dy is inert here).
if scene_info.get("cable_xy_offset", (0.0, 0.0))[0] != 0.0:
    _cx_near = state.body_q.numpy()[cable_bodies, 0][np.abs(_cy_all - _grasp_at) < 0.10]  # SAME grasp-region mask
    if _cx_near.size:
        x_grasp = float(np.mean(_cx_near))
    print(f"  [S6_ROUTE] caveat-a-X: settled-cable-X x_grasp={x_grasp * 1e3:+.2f}mm "
          f"(nominal GRASP_X={GRASP_X * 1e3:+.0f}mm, delta={(x_grasp - GRASP_X) * 1e3:+.2f}mm)")
```
Reuses `_cy_all` (:3864) + `_grasp_at` (:3862) for the identical mask. Precedes all consumers (:3881→). NOTHING ELSE.
