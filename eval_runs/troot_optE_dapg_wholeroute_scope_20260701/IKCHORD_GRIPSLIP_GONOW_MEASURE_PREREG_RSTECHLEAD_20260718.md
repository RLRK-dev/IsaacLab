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

---

## CORRECTION v2 — 2026-07-18 15:37 JST (evidence-readiness, OPS-SUP conditions)

The initial legs (M1/M2/M3) + an unauthorized FF-no-pin leg (M2b) were run with a harness that omitted prereg-required provenance and did not enforce a fresh outbox, and M2b was not registered here. Per OPS-SUP (15:12 / 15:21) those runs are **DIAGNOSTIC history only, EXCLUDED from evidence**; the marked outboxes (`gonow_20260718/*`, `ff_nopin_wholeroute/ABORTED_UNAUTHORIZED.txt`) are retained untouched. The evidence set is produced by a **fresh rerun** under the conditions below.

### Harness (banked, evidence-grade)
`thread_isaac_lab/scripts/gonow_measure.py` commit **`c4253ed4`**, sha256 **`83342dc2…`**. Fail-closed, it now:
- embeds argv / pid / venv_python / MUJOCO_GL / `cvd` (CVD env) / requested_device / git HEAD + dirty-porcelain / recording sha256 into `summary.provenance`;
- computes a pre/post repo **source closure** from `sys.modules` with `changed_source_set`/`missing_source_set` (both must be `[]`) plus a **harness self-sha pre==post** hard bar;
- **exits 2** if the outbox leaf already exists (fresh-outbox bar); the launcher writes `run.log` to the **parent** dir and passes a **non-existent leaf**;
- writes a `COMPLETE.ok` marker LAST and returns **non-zero** on any integrity violation or existing outbox.

### Prior-art / no-repeat disposition (OPS-SUP cond 2)
`check_thread_vault_prior_art.sh --fail-on-blocker grip-slip ik_chord B4-shadow necessity` returned BLOCKER, but every match is in **this arc's own banked design** (`IKCHORD_GRIPSLIP_FORCEDESIGN_VTDESIGN §10.10/§10.12` — the B4-shadow spec + B5 split) — a **self-match of the current design that authorizes these measurements**, NOT a repeat of a failed path. The one prior failure in this arc (the **substep-decouple** plan) is REFUTED and is **not** what is rerun. **Concrete delta** from the diagnostic runs = the provenance-complete, integrity-fail-closed, fresh-outbox harness above (the *evidence-grade* rerun).

### M2b — FF-no-pin whole-route (REGISTERED, OPS-SUP cond 1)
- **Question:** is the M2 FF+pin drop@347 (`B_contact_loss`) caused by the pin (welding C1 displaces the cable → recorded arms lose it) or intrinsic to the FF/recorded branch?
- **Purpose:** ATTRIBUTION of the M2 drop; isolates the recorded-branch grip WITHOUT the pin confound.
- **Exact config:** `--drive-mode feedforward` (NO `--route-c1-pin`, NO `--shadow`) `--episode-steps 900`, GOLDEN recording, wc=1, `INIT_XY_NOISE=0.0`, fresh outbox.
- **Falsifiable binary bar:** FF-no-pin **holds past step 347** (no drop through ≥ the M2 window) → the **pin** caused the M2 drop (a `(d-a)/(d-b)` finding, flagged to p5); **OR** FF-no-pin **also drops ≲ ~347** → the recorded branch itself does not hold whole-route (a #18 coverage concern).
- **Conjoin:** interpreted ONLY against M2 (FF+pin); the pair is the attribution — a single-leg number is not a verdict.
- **Alone does NOT discharge any gate:** M2b is attribution/diagnostic for the coverage question; the pre-impl coverage gate (CC2 CH-1) is only informed, not discharged (whole-route ik_chord efficacy = B5b, post-impl).

### Evidence rerun set + order (OPS-SUP cond 7)
harness bank (done) → OPS-SUP commit readback → THIS prereg+M2b bank → OPS-SUP scope PASS → **fresh rerun**. Rerun = M1 (B4-shadow ik_chord+pin) · M2 (FF+pin+shadow: coverage + positive control) · M2b (FF-no-pin attribution) · M3 (ik_chord natural-term). Each to a **fresh leaf** with `run.log` in the parent. B6-char / B5b / impl remain UNAUTHORIZED.
