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

---

## CORRECTION v3 — 2026-07-18 16:19 JST (harness PASS-CLOSE; M2b one-variable + exact 3-state + pre-fire trace)

The evidence-grade harness is **OPS-SUP PASS-CLOSE** at **commit `78d2b94c`**, `gonow_measure.py` sha256 **`de44d4a1dce37cedf93e9582dffab7f5d2dd19df0bb7d9164ec34813809a732`** (1-path, working-tree clean, `device_provenance_ok` a hard bar). This v3 **SUPERSEDES** the v2 §Harness hash and the v2 M2b binary bar.

### Evidence-grade harness (final)
`commit 78d2b94c` / sha256 `de44d4a1…`. All v2 provenance PLUS an **enforced device hard bar**: before the drive it exit-2s unless `--device=cuda:N`, `sys.prefix==/home/rlrk/env_isaaclab7`, CVD non-empty, `torch.cuda.is_available`, no probe error, `str(env.device)==cuda:N`, `current_device==N` (CVD-visible namespace), `device_count>N`; `device_provenance_ok` is conjoined into `source_integrity_ok`, so `status=COMPLETE` implies it. The earlier 5-step `/tmp` provsmoke is **DIAGNOSTIC / NON-EVIDENCE** (pre-bank + no `cvd` field). Prior-art concrete delta = **this** harness (`78d2b94c`), not the superseded `c4253ed4`.

### M2b — FF-no-pin, ONE-VARIABLE (SUPERSEDES v2 M2b)
- **Config:** `--drive-mode feedforward` **`--shadow`** (NO `--route-c1-pin`) `--episode-steps 900`, GOLDEN, wc=1. So M2 (FF+pin+shadow) and M2b (FF+shadow, no-pin) differ in **exactly** `route_c1_pin`. **Hard-assert** in analysis: M2 and M2b provenance agree on harness sha / source-closure / recording sha / venv / effective device / `RL_SIM_SUBSTEPS` / `PHYSICS_STEPS_PER_RL` / horizon / drive_mode, and the effective-config diff set = **{`route_c1_pin_effective`, `pin_seat_seg`}** only. Any other diff → INCONCLUSIVE.
- **Frozen anchor:** step **347** (`B_contact_loss`) is a POST-DIAGNOSTIC frozen anchor from the diagnostic M2 run; attribution window = steps **[242 (g3; pin-fire ≈246) .. 347]**.
- **Causal precondition — pre-fire trace equality:** M2 and M2b per-step drop-metric traces (`contact_r`, `contact_l`, `held_z_minus_rest`, `dx_c1`, `g_latched`, `held_i`) must be **equal from route step 0 through the pin-fire step (~246)**. If they diverge before ~246, `route_c1_pin` is not the isolated variable in the drop window → **INCONCLUSIVE** (route_c1_pin also alters build-time bank prep).
- **Exact three-state classification (no `≲`/`~`):**
  - **PIN-ASSOCIATED:** pre-fire traces equal ∧ M2 drops (`B_contact_loss`) within [246..347] ∧ M2b does **not** drop through step 347 (no `B_contact_loss` in [246..347]).
  - **BRANCH-INTRINSIC:** pre-fire traces equal ∧ M2b **also** drops in [246..347] with the **same** cause (`B_contact_loss`) — the recorded branch loses grip whole-route, pin-independent.
  - **INCONCLUSIVE:** pre-fire traces diverge, OR M2b drops with a different cause or outside [246..347], OR any `device_provenance_ok`/`source_integrity_ok`/config-diff-set assertion fails on either leg.
- **Alone does NOT discharge any gate:** M2b is attribution for the coverage question; the pre-impl coverage gate (CC2 CH-1) is only informed (whole-route ik_chord efficacy = B5b, post-impl).

### Evidence rerun set (final)
M1 (B4-shadow ik_chord+pin+shadow) · M2 (FF+pin+shadow) · M2b (FF+**shadow**, no-pin) · M3 (ik_chord natural-term). Each: fresh leaf, `run.log` in the parent, `--device cuda:0` with `CUDA_VISIBLE_DEVICES=0`. Order: THIS prereg bank → OPS-SUP scope PASS → prior-art readback → rerun. B6-char / B5b / impl UNAUTHORIZED.

---

## CORRECTION v3.1 — 2026-07-18 16:55 JST (OPS-SUP prereg-v3 scope readback: B1 causal boundary + B2 disjoint/exhaustive 3-state + B3 executable commands)

OPS-SUP prereg-v3 scope readback (16:46 JST) = **HOLD**: harness pin (`78d2b94c` / `de44d4a1`) + one-variable config PASS; run fence CLOSED pending three **records-only** corrections (no harness change, no sim). This v3.1 **SUPERSEDES** the v3 §"Causal precondition — pre-fire trace equality" (~246 wording) + §"Exact three-state classification" and adds the executable command block. Anchors are **grounded on-disk** against the diagnostic summaries (NON-EVIDENCE, `gonow_20260718/`): M2 `ff_wholeroute` `first_shadow_fire=246`, `g3_step=242`, `done_step=347`, cause `B_contact_loss`; M2b `ff_nopin_wholeroute` `done_step=342`, cause `C_c1_escape`.

### B1 — causal boundary (CRITICAL): the pin-intervention step f is EXCLUDED from the equality window
- **f := M2 `summary.shadow.first_shadow_fire_step`** (the read-only detection of the (d-b) fire; in M2/FF the real weld fires the same step via `:1225`). **Frozen diagnostic expectation: `f == 246`** (grounded: diagnostic M2 `first_shadow_fire=246`). **Any other f → INCONCLUSIVE** (anchor moved).
- **Pre-fire trace equality is on `per_step.step ∈ [0, f-1]` ONLY** (rollout rows strictly BEFORE f), NOT through f. Rationale: the real pin intervention (weld) occurs DURING step f, so M2 and M2b legitimately diverge from f onward — requiring equality AT f would reject the causal effect itself. All "~246"/"≈246"/route-step-ambiguous language is replaced by **f** + explicit **`per_step.step`** integer indices (pre-fire window = rows 0..245).
- Compared fields per row (both legs, exact equality): `contact_r, contact_l, held_z_minus_rest, dx_c1, g_latched, held_i, grasped, contact_loss_count`.

### B2 — disjoint + exhaustive three-state (HIGH): common validity predicate P first
Per leg, from the harness summary: `term_step = done_step`; `term_cause` = the cause k∈{`A_held_z_floor`,`B_contact_loss`,`C_c1_escape`,`explosion`} with the smallest non-null `first_cause_step[k]` (None if the leg never terminates through its horizon).

- **P (common validity predicate)** — REQUIRED for any non-INCONCLUSIVE verdict: both M2 and M2b `status==COMPLETE` ∧ `provenance.source_integrity_ok` (⊇ `device_provenance_ok`) on BOTH ∧ the run-independent provenance-equality assertion (§B3) ∧ config-diff-set == `{route_c1_pin_effective, pin_seat_seg}` only ∧ **f == 246** ∧ **exact per_step equality on [0, f-1]** (§B1).
- **PIN-ASSOCIATED** = P ∧ [M2: `term_cause==B_contact_loss` ∧ `term_step ∈ [f, 347]`] ∧ [M2b: **no terminal of ANY cause through step 347** — `term_step is None` or `> 347`].
- **BRANCH-INTRINSIC** = P ∧ [M2: `term_cause==B_contact_loss` ∧ `term_step ∈ [f, 347]`] ∧ [M2b: `term_cause==B_contact_loss` ∧ `term_step ∈ [f, 347]`] (both legs same B-cause terminal in-window → recorded branch loses grip pin-independently).
- **INCONCLUSIVE** = every remaining outcome (the complement), explicitly including: M2 has no `B_contact_loss` terminal in `[f,347]`; **either leg terminates by an other cause** (`A_held_z_floor`/`C_c1_escape`/`explosion`); M2b `B_contact_loss` outside `[f,347]`; or any P conjunct fails.

The three are **disjoint** (PIN-ASSOCIATED requires M2b to have NO terminal through 347; BRANCH-INTRINSIC requires an M2b B-terminal in-window ⊂ "some terminal"; INCONCLUSIVE = complement) and **exhaustive** (INCONCLUSIVE = complement). This removes the v3 overlap where an M2b other-cause terminal satisfied both the "no B_contact_loss" PIN-ASSOCIATED wording AND INCONCLUSIVE.

**Diagnostic-informed, NON-EVIDENCE (does NOT force the fresh verdict):** the diagnostic M2b dropped `C_c1_escape@342` (an other-cause terminal ≤347) → under the strict rule the fresh rerun is **expected to classify INCONCLUSIVE** (M2b other-cause terminal). Mechanically correct: the pin-vs-branch binary does not cleanly resolve because FF-no-pin fails for a THIRD reason (C1 escape after seat) — itself a coverage finding for CC2 CH-1 / p5 (recorded branch does not hold C1 whole-route even pin-OFF). The fresh legs produce the actual verdict; this note only prevents a forced PIN-ASSOCIATED read.

### B3 — executable prereg (HIGH): the four literal commands (banked before prior-art/run)
Fresh parent (does not exist): `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/gonow_evidence_20260718/` (distinct from the diagnostic `gonow_20260718/`). Preamble once: `mkdir -p "$P"`. Each leg passes a **non-existent leaf** (`--outbox`) — the harness `exit 2`s if it pre-exists (fresh-outbox bar); `run.log` is written to the **parent** with a per-leg name; **no tee** → command rc == interpreter rc == the harness machine-decidable exit (0 COMPLETE / 2 provenance-violation / 3 source-integrity). Horizon `--episode-steps 900` (whole-route cap; each leg breaks at its natural terminal). `--recording` pinned to the GOLDEN npz.

```bash
cd /home/rlrk/IsaacLab
P=eval_runs/troot_optE_dapg_wholeroute_scope_20260701/gonow_evidence_20260718
G=eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz
mkdir -p "$P"

# M1 — B4-shadow (ik_chord + pin + shadow): necessity (expect shadow-fire=0 ∧ g3=false)
CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
  thread_isaac_lab/scripts/gonow_measure.py --device cuda:0 --episode-steps 900 --recording "$G" \
  --drive-mode ik_chord --route-c1-pin --shadow \
  --tag m1_b4shadow --outbox "$P/m1_b4shadow_ikchord" > "$P/run_m1_b4shadow.log" 2>&1

# M2 — FF + pin + shadow: coverage baseline + positive control (expect f=246, drop B@347)
CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
  thread_isaac_lab/scripts/gonow_measure.py --device cuda:0 --episode-steps 900 --recording "$G" \
  --drive-mode feedforward --route-c1-pin --shadow \
  --tag m2_ff_pin --outbox "$P/m2_ff_pin_shadow" > "$P/run_m2_ff_pin.log" 2>&1

# M2b — FF + shadow, NO pin: one-variable attribution (differs from M2 only in --route-c1-pin)
CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
  thread_isaac_lab/scripts/gonow_measure.py --device cuda:0 --episode-steps 900 --recording "$G" \
  --drive-mode feedforward --shadow \
  --tag m2b_ff_nopin --outbox "$P/m2b_ff_shadow_nopin" > "$P/run_m2b_ff_nopin.log" 2>&1

# M3 — ik_chord natural-termination (B5a): current reachability (expect drop A@267)
CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
  thread_isaac_lab/scripts/gonow_measure.py --device cuda:0 --episode-steps 900 --recording "$G" \
  --drive-mode ik_chord \
  --tag m3_ikchord_natterm --outbox "$P/m3_ikchord_natterm" > "$P/run_m3_natterm.log" 2>&1
```

**Run-independent provenance-equality assertion (M2 vs M2b, analysis-time):** equal on `provenance.harness_self_sha256_post`, `provenance.source_closure_run_end` (∧ `changed/missing/added_during_drive/build_added_unstable == []`), `provenance.recording_sha256`, `provenance.venv_python`, effective device (`current_device`/uuid), `effective_config.RL_SIM_SUBSTEPS`, `.PHYSICS_STEPS_PER_RL`, `.drive_mode`, `episode_steps_requested`; effective-config diff-set == `{route_c1_pin_effective, pin_seat_seg}` ONLY. **Run-specific, NOT asserted equal:** `argv`, `pid`, `tag`, `outbox` (differ per leg by design).

**Order (unchanged):** THIS v3.1 bank → OPS-SUP scope readback → prior-art readback (concrete delta = harness `78d2b94c`) → fresh rerun. Records-only; no harness change, no sim. B6-char / B5b / impl remain UNAUTHORIZED; execution HOLD; training-ready LOCKED; WMSO untouched (released to pQ).

---

## CORRECTION v3.2 — 2026-07-18 17:08 JST (OPS-SUP prereg-v3.1 readback: C1 command-block fail-closed + C2 co-terminal cause set + P row-completeness)

OPS-SUP prereg-v3.1 readback (17:01 JST) = **HOLD (narrow, records-only)**: B1 causal-f boundary + B2 main disjoint/complement logic PASS; the four outbox paths are absent (fresh) and the `78d2b94c` pins/commands read correctly. Two fail-closed gaps remain. This v3.2 **SUPERSEDES** the v3.1 §B3 command-block preamble and the v3.1 §B2 `term_cause` (smallest-non-null) definition. No harness change, no sim.

### C1 — command block fail-closed (HIGH): fresh-parent bar + set -e sequencing
v3.1 used `mkdir -p "$P"` (**silently accepts a pre-existing parent**) and the four sequential legs had **no `set -e`** — an M1/M2/M2b nonzero rc was preserved only in that leg's local rc while the block continued, so the block's final rc could be M3's (masking an earlier integrity/provenance abort).

**Frozen preamble (SUPERSEDES the v3.1 §B3 preamble):**
```bash
set -euo pipefail
cd /home/rlrk/IsaacLab
P=eval_runs/troot_optE_dapg_wholeroute_scope_20260701/gonow_evidence_20260718
G=eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz
test ! -e "$P"   # fail-closed fresh-PARENT bar (complements the harness fresh-LEAF exit-2)
mkdir "$P"       # plain mkdir (NOT -p): errors if $P exists or the grandparent is missing
```
The four leg commands (M1→M2→M2b→M3) are unchanged in flags/outbox/tag/redirect, but now run **under `set -e` with direct redirection (no tee)** → each harness nonzero exit (2 provenance / 3 source-integrity) **aborts the block before the later legs run** (fail-closed sequencing; an M1 integrity abort never silently proceeds to M2). The block rc == the first failing leg's rc.

### C2 — co-terminal cause set (HIGH): term_cause_set + P row-completeness
The v3.1 `term_cause = argmin non-null first_cause_step[k]` is **ambiguous when ≥2 causes share `done_step`** (co-terminal). Replace with a set:
- **`term_cause_set = {k ∈ {A_held_z_floor, B_contact_loss, C_c1_escape, explosion} | first_cause_step[k] == done_step}`** (the cause(s) active exactly at the terminal step; `∅` if `done_step is None`). Grounded: harness sets `first[k]=t` at the first true frame and `done_step=t` at the break (`gonow_measure.py:364-375`), so a cause with `first_cause_step[k]==done_step` is active at termination.
- A leg is a **clean-B terminal in-window** iff `done_step ∈ [f, 347]` **∧** `term_cause_set == {B_contact_loss}` (B is the **sole** cause at the terminal step). **Empty / multiple / co-terminal `term_cause_set` → INCONCLUSIVE** for any B-claim.

**P (updated):** additionally require **both legs' `per_step` contain every integer index in `[0, f-1]`** (all pre-fire rows present; `per_step[i].step==i`, `:369`) before the exact row comparison; **any missing index → P failure** (a leg that terminated before `f` cannot supply the pre-fire trace).

**Three-state (restated with `term_cause_set`; SUPERSEDES the v3.1 §B2 verdict clauses):**
- **PIN-ASSOCIATED** = P ∧ [M2 clean-B terminal in-window] ∧ [M2b: `done_step is None or done_step > 347` — no terminal of any cause through 347].
- **BRANCH-INTRINSIC** = P ∧ [M2 clean-B terminal in-window] ∧ [M2b clean-B terminal in-window].
- **INCONCLUSIVE** = complement — explicitly incl. any B-claimed leg with `term_cause_set` empty/multiple/≠`{B_contact_loss}` in-window; M2b any terminal ≤347 that is not a clean-B (defeats BRANCH); M2b `B` outside `[f,347]`; missing pre-fire rows; `f != 246`; or any P conjunct failing.

**Diagnostic-informed, NON-EVIDENCE (conclusion unchanged, restated in the set framing):** diagnostic M2 `first_cause_step={B:347}` → `term_cause_set={B_contact_loss}` clean-B@347 ∈ [246,347] ✓; diagnostic M2b `first_cause_step={C_c1_escape:342}` → `term_cause_set={C_c1_escape}` ≠ {B}, a terminal ≤347 → PIN-ASSOCIATED fails (M2b has a terminal) **and** BRANCH-INTRINSIC fails (not clean-B) → **INCONCLUSIVE**. Baked, not forced; the fresh legs produce the verdict.

**Order (unchanged):** THIS v3.2 bank → OPS-SUP scope PASS (opens the **prior-art readback**, NOT the run) → prior-art readback → fresh rerun. Records-only; no harness change, no sim. B6-char / B5b / impl UNAUTHORIZED; execution HOLD; training-ready LOCKED; WMSO untouched (pQ).
