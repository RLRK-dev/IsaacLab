# #18 GRIP — GO-NOW MEASUREMENT PREREG (read-only [VERIFY], pre-impl)

**Author (CC1):** RS-TECH-LEAD (w2:p4). **Stamped:** 2026-07-18 14:38 JST.
**Authorized set** (OPS-SUP scope verdict 13:51 + adoption readback PASS 14:32; p5 §10.12 spec + GO-now ACK): **B4-shadow + FF whole-route + ik_chord-natural-term (B5a)**.
**NOT authorized / deferred (separate auth):** B6-char (basin/A1 threshold), B5b (post-fix whole-route), impl.
**Governing:** DDR #18 `00-DESIGN-STATUS-LEDGER.md:98` (execution HOLD; read-only [VERIFY] confirmed in-HOLD by OPS-SUP). L3 verdict `IKCHORD_GRIPSLIP_FIX_L3_DEBATE_VERDICT_RSTECHLEAD_20260718.md`. Design `IKCHORD_GRIPSLIP_FORCEDESIGN_VTDESIGN_20260718.md` §10.8-§10.12.

## Constraints (OPS-SUP)
- **No env-source edit** (`envs/` untouched); measurement scripts only; read-only observation hooks (instance-attr wrap, like `measure_grip_retention.py`'s `_reset_worlds` hook).
- Per run: **fresh outbox**, **effective env config recorded from the LIVE env** (not module constants — closes the L3 false-provenance gap), recording sha256, exact argv, harness_self_sha, loaded-source closure, `MUJOCO_GL=egl`, `env_isaaclab7` venv, `CUDA_VISIBLE_DEVICES` pinned.
- **prereg/bank before run.**

## M1 — B4-shadow (necessity corroboration of CC6; complements §10.11 segment analysis)
- **Question:** would the (d-b) C1 pin fire before the drop under ik_chord? (If not, the pin can't moot the grip fix → fix necessary.)
- **Method:** wc=1 **ik_chord** env, `route_c1_pin=True` (arms the pin → sets `_pin_seat_seg`; the ik_chord loop has NO `_maybe_activate_c1_pin` call, so it never fires). Wrap `_physics_step_all` **read-only**: BEFORE each physics frame compute the shadow fire predicate faithfully (p5 §10.12 / `:1848-1855`):
  `seat_body = cable_bodies[0][_pin_seat_seg]` → `seat_world = bq[seat_body,:3]` → `capture = rex.clip_capture_check(solver, seat_world)` → `depth = seat_world[2] <= Z_FIRE_DEPTH_M (0.831)` → `fire = capture ∧ depth` (either False resets dwell) → **shadow-fire when consecutive-dwell ≥ PIN_TRIGGER_DWELL_K (3)**. **NEVER call `authorize_clip_pin`** (no weld/authorizer/physics change; observe count only).
- **Falsifiable outcome:** shadow-fire count at frames before the drop step (267). **shadow-fire=0 ∧ g3=false → necessity discharged** (pin can't fire pre-drop). **shadow-fire>0 → real pin counterfactual needed = separate gate** (would still require the §10.11 segment analysis: even a fired pin holds C1, not the gripper-midpoint `held_i`).
- **Positive control (anti-self-proof):** the SAME shadow observation on the **FF** drive (which DOES seat C1 and fires the pin at `:1225`) MUST show **shadow-fire>0** — proving the detector can come out non-zero. (= M2's FF run with the shadow hook.)

## M2 — FF whole-route (coverage baseline [CC2 CH-1] + M1 positive control)
- **Question:** does FF grip through the whole route incl. C2_REGRASP (~step 500) to G6? (No full-route FF baseline exists.)
- **Method:** wc=1 **feedforward** env, drive to ~900 steps (whole route; `MAX_EPISODE_STEPS=900`). Re-derive drop metrics (mirror `:1653-1660`). Run WITH the B4-shadow hook + `route_c1_pin=True` → the positive control (shadow-fire>0 expected once C1 seats).
- **Falsifiable outcome:** FF holds dual grip to G6 (no drop) → recorded branch valid whole-route (supports the fix premise). FF drops at C2_REGRASP → the recorded branch is NOT whole-route-valid (deeper issue, escalate).

## M3 — ik_chord natural-termination (B5a)
- **Question:** current ik_chord reachability across the route.
- **Method:** wc=1 **ik_chord**, `route_c1_pin=False`, drive to natural term; record drop step + first cause.
- **Falsifiable outcome:** drops@267 (`A_held_z_floor`) → B5a = **BLOCKED_BY_PRE_C2_DROP**; C2_REGRASP unreachable pre-fix → B5b (post-fix whole-route) deferred.

## Discharges / defers
- **Discharges:** CC6 necessity (M1 + §10.11) · CC2 coverage baseline (M2) · B5a reachability (M3).
- **Defers (separate auth):** B6-char (basin/A1 threshold — A1 vetted threshold-TBD in re-debate, tuned post-auth), B5b (post-fix), impl.
- **After:** results → B6-char auth decision → re-debate (L3) v2.1 WITH evidence → (if PASS) rule-check → impl (Rs sign-off + §C ratify).
