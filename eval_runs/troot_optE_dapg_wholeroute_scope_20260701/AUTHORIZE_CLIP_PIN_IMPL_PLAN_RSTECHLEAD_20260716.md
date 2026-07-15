# authorize_clip_pin — implementation plan + [VERIFY] (RS-TECH-LEAD %12, 2026-07-16)

Node `T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild`. L3. Impl=%12, verify-leg=p1, design=p5 (§15 BANKED `cc9ebf3b1e`).
Governing design = `RLENV_PIN_DESIGN_VTDESIGN_20260715.md` §15 (read order §17→§19→§16→§15; §12 SUPERSEDED, §14.1 retracted §17).
Rs directive: implement in fresh session (2026-07-16); INVARIANT #5 clip-only RL-env scope BANKED `4de2c9fd42` (RS71 §0:28).

## Grounding (on-disk, cited)

| item | cite | value |
|---|---|---|
| eq single writer (wraps) | `route_executor.py:727` `activate_c1_pin(solver, seat_body, seat_world)` | world-pos match, RAISE on fail, returns witness |
| pin-candidate filter | `route_executor.py:771-774` | `eq_type==CONNECT ∧ eq_obj2id==0 ∧ eq_active0==0` |
| ref 4-leg gate (point-in-box) | `route_executor.py:3074-3078` | lat 3.5 / dom≤y_win(15) / 821<z<836 on a POINT `_seat_w` |
| selector (nested, non-reusable) | `route_executor.py:2190-2202` | worldbody BOX, 30mm XY box → module-level `clip_geoms_at` |
| bars (built-model) | `route_env_config.py:156-158` | SEAT_LAT_BAR_M 0.0035 / SEAT_Z_LO_M 0.821 / SEAT_Z_HI_M 0.836 |
| route clip centres | `route_env_config.py:139-140` | ROUTE_C1_XY (0.35,0.150) / ROUTE_C2_XY (0.40,0.000) |
| pin eq prealloc (per body, DISABLED) | `newton_skill_env_base.py:1595-1603` | default OFF = byte-identical |
| RL env firing (WORLD-0) | `newton_route_env.py:1711-1722` `_maybe_activate_c1_pin` | `_cable_bodies[0]`, single witness |
| support-clip trap | design §14.1 / `newton_skill_env_base.py:1822-1829` | jigs x=0.30, band (801,816), route env ON |

## 5-piece implementation

**① `route_env_config.py`** — add after :140:
```python
ROUTE_CLIP_CENTERS = (ROUTE_C1_XY, ROUTE_C2_XY)   # authorized set; 5-clip = extend THIS one tuple (§15.1/§15.2)
```
+ export (append to the module's public list; add to `_ROUTE_OWNED_PARAM_NAMES` guard set).

**② `route_executor.py`** — new (near `activate_c1_pin`):
- `class BrokenSelector(RuntimeError)` / `class NotInAnyRouteClip(RuntimeError)` — RAISE, never "unseated".
- `clip_geoms_at(mjm, mjd, cx, cy, xy_tol=0.03)` — module form of `_clip_geoms` (worldbody BOX ≤30mm of centre).
- `clip_capture_predicate(seat_world, cx, cy, lat_bar_m, y_win_m, z_lo_m, z_hi_m) -> (bool, reason)` — PURE, 3 legs (lat/dom/z), reason names failing leg. Unit-testable = N1-N7.
- `authorize_clip_pin(solver, seat_body, seat_world, match_tol_m=5e-3)` — imports `rc.ROUTE_CLIP_CENTERS`; per centre: `clip_geoms_at`→count∈{5,6} else `BrokenSelector`; `y_win=max(geom_size[g][1])`; `clip_capture_predicate` with `rc.SEAT_*`; on pass → `activate_c1_pin(...)` (single writer); else `NotInAnyRouteClip`.
- `audit_pin_anchors(mjm, mjd)` — episode-end (§15.4): fired pins = filter ∧ `eq_active==1`; `len(fired) ≤ len(ROUTE_CLIP_CENTERS)`; each `eq_data[3:6]` inside ∃c capture volume else `AssertionError`.

**③ `newton_route_env.py:1722`** — `rex.activate_c1_pin(...)` → `rex.authorize_clip_pin(...)` (same args/return).

**④ `newton_route_env.py` step (done block, ~:1803)** — `if self._route_c1_pin: rex.audit_pin_anchors(self._solver.mj_model, self._solver.mj_data)` BEFORE `_reset_worlds` (guarded → byte-neutral when pin OFF).

**⑤ N1-N7 controls** — new script `authorize_clip_pin_controls.py`: build route-env scene (perclip_pin), run:
| # | seat | axis | expect | catches |
|---|---|---|---|---|
| P1 | C1, z=829.68 | — | ACCEPT | golden |
| P2 | z=830.0 | z | ACCEPT | arch float |
| N1 | z=880.9 | z+ | REJECT | aerial |
| N2 | z=816.0 | z− | REJECT | under clip |
| N3 | x=C1x+4.0mm | x | REJECT | outside wall (3.5) |
| N4 | y=C1y+20mm | y | REJECT | outside y-win (15) |
| N5 | (0.300,+0.050,0.810) support | set | NotInAnyRouteClip | ①support-clip trap (z-only blind) |
| N6 | (0.400,0,0.829) built C2 | set | ACCEPT | set content |
| N7 | task_config C2 (0.40,+0.075) in set | selector | BrokenSelector | ④scene↔task drift |
+ grep test: `eq_data\[`/`eq_active\[` writers (authorize→activate_c1_pin is the single write path).
+ byte-repro: pin OFF (default) → build byte-identical (no behavior change).

## [VERIFY] adversarial failure-mode analysis (CC1 self-review; infra may stall sub-agent per handoff:34)

| FM | scenario | verdict | evidence / mitigation |
|---|---|---|---|
| A | frame-0 seat in support clip (x=0.30) welded | SAFE | ROUTE_CLIP_CENTERS excludes x=0.30 (selector 50/100mm>30mm) + lat bar 3.5 rejects + floor 821 rejects band (801,816). N5. |
| B | selector wrong count on route env | GUARDED | count∈{5,6} → BrokenSelector; N6/N7 verify empirically. |
| C | y_win derivation wrong | VERIFY | `max(geom_size[g][1])`==producer :3040 (=15mm, LEDGER:55). N4 (20>15 REJECT) tests. |
| D | NOT byte-neutral when pin OFF | VERIFY | all new paths gated by `route_c1_pin` (default False); byte-repro control. |
| E | authorizer RAISEs on legit C1 onset seat (regression) | VERIFY | onset seat dx0.37/z828.8 (LEDGER:55 seated=True) → ACCEPT; g6_live rollout confirms fire. IF raise = correct refusal (unseated), = finding not bug. |
| F | count assert fires on golden's 6 structural eqs | SAFE | filter `eq_obj2id==0 ∧ eq_active0==0` isolates pin candidates; fired=1 (world0) ≤2 (§15.3/§14③). |
| G | mj_forward perturbs sim | SAFE | read-only refresh (activate_c1_pin already does :766). |
| H | audit reads cleared eq table | SAFE | runs BEFORE _reset_worlds; anchor is in mjm.eq_data (fixed at fire), not data. |
| K | exception swallowed → guarantee lost | SAFE | RL env calls direct (no try/except); raise = loud run-crash (intended). |
| **L** | **multi-world firing (permanent wiring)** | **SURFACE** | current firing = WORLD-0 (d2 scaffold). 5-piece wraps :1722 only. All-world firing = separate change, couples to g6_live rollout/W1 training. → p5/Rs scope, NOT this task. |

## Open questions (surface, do not silently decide)
- **Q-L (multi-world firing):** "恒久配線" for training needs all-world firing; current is world-0. 5-piece = authorizer + world-0 wrap (per handoff:32). Multi-world = follow-up (p5 design + p1/Rs training-readiness). g6_live rollout here = world-0 validation of authorizer + FM1 causal chain.

## Gate status
[L-TRIAGE] L3 ✓ → [VERIFY] this doc (CC1 self + independent pre-check) → [RULE-CHECK] stage2 → [CHANGE] → [RUN N1-N7] → g6_live rollout (FM1). Prior-art guard PASS. RS71 §0 clip-only scope CONFIRMED.

---

## [VERIFY] OUTCOME (independent pre-check, 2026-07-16) — verdict PROCEED-WITH-FIXES

Independent /pre-check sub-agent (206k tok, 35 tool-uses, on-disk grounded) corroborated the core mechanism
(count-filter triple-discriminated, y_win=15mm uniform, support-clip trap SAFE, golden onset ACCEPT, byte-neutral)
and returned **PROCEED-WITH-FIXES**. Findings + resolution:

- **[MAJOR] F1 "permanent wiring" NOT delivered** — the (d2) firing scaffold I wrap fires ONCE (world-0, FF-replay,
  ep1): `_c1_pin_witness` scalar never reset in `_reset_worlds`; `eq_active` never cleared → weld persists across
  resets. ⇒ **SCOPE CORRECTED (below). Not a code bug in the authorizer; a property of the scaffold it gates.**
- **[MAJOR] F2 single-writer not repo-wide** — 4 eq writers exist (`route_executor.py:794`/:3140, `policy_route_runner.py:328`,
  `test:4798`); piece ③ reroutes only the RL-env caller. ⇒ audit = **RL-env-path guarantee**, not repo-wide. The
  §12.354 "writer count == 1" grep is NOT a control here (dropped from piece ⑤; the audit supersedes it, §15.4).
- **[MAJOR] F3 multi-world clip count** — RESOLVED: `solver.mj_model` is the **single-world mujoco template** (neq=46),
  so `clip_geoms_at(C1)=5, C2=6` at world_count=1 AND 4 (verified). Count assert is world_count-agnostic. ✓
- **[MAJOR/low-risk] F4 §15.1 loop-form vs §19 `clip_xy`-arg-form** — I implemented §15.1's imported-set loop (per
  handoff:30/32; stronger: caller cannot name a clip). §19 (later) adopts %12's `clip_xy` arg + membership check.
  Both are safety-equivalent for the single-C1 fire. ⇒ **SURFACE to p5 (design authority) — confirm loop-form OK.**
- **[MINOR] F5** audit bound `≤len(ROUTE_CLIP_CENTERS)` is world-0/1-episode-scoped; near-vacuous under F1's stale weld → part of the F1 follow-up.
- **[MINOR] F6 byte-neutrality** — the audit's `import route_executor` sits INSIDE the `route_c1_pin` guard. ✓ correct.
- **[MINOR] F7 (d2) do-not-touch** (`newton_route_env.py:1694`, LEDGER:52 confound control) — Rs permanent-wiring
  directive supersedes; a RAISE-capable gate could turn "pin-held" into "pin-refused" on a borderline rollout ⇒
  g6_live reports the LIVE onset dx/dy (not just the producer's 0.37/3.17).
- **[MINOR] F8 denominator** — 58/486 (58 aerial + 60 unseated of 486 pinned; LEDGER:52), not 58/343; FM-E's
  dx0.37/z828.8 is the PRODUCER value.

## ⭐ SCOPE CORRECTION (F1) — what this task DOES and does NOT deliver

DELIVERS: the **clip-only pin AUTHORIZER** (`authorize_clip_pin` + capture predicate + selector + episode-end
anchor audit), wired into the existing (d2) RL-env firing path, validated at unit/mechanism level (N1-N7 14/14)
and single-episode/world-0 live (g6_live). "Clip only" is now a MECHANISM (imported `ROUTE_CLIP_CENTERS`), not
caller discipline.

Does NOT deliver training-ready "permanent wiring". Rs's directive「クリップのみ pin を RL env に恒久配線」has two
parts: (1) clip-only [DONE = the authorizer]; (2) 恒久配線 [permanent] = generalising the FIRING SCAFFOLD, which the
§15 design/5-piece do NOT cover. Four lifecycle gaps remain, each a SURFACED follow-up (design=p5, scope=Rs):
  (a) `_c1_pin_witness` reset per episode (else the pin fires once per env lifetime);
  (b) `eq_active` cleared on `_reset_worlds` (else ep1's weld persists / re-triggers the audit trivially);
  (c) multi-world firing (current = world-0 `_cable_bodies[0]`; the mujoco template is single-world);
  (d) policy-drive path (current firing is in the recorded-FF drive loop `:1194→:1203`, not the RL policy drive).

⇒ **W1 training launch is NOT unblocked by this task alone**; it also needs the (a)-(d) scaffold generalisation +
FM3/FM4 tighten + demos regen (per LEDGER:57). This task closes the AUTHORIZER leg of the pin work.

## N1-N7 controls RESULT (2026-07-16, CPU)
`authorize_clip_pin_controls.py` → **14/14 ALL PASS** (`authorize_clip_pin_controls_result.json`). Built-model bars
lat=3.50 / z=(821,836) / y_win=15.00mm; geoms C1=5 C2=6. P1/P2 ACCEPT; N1(z880.9)/N2(z816)/N3(dx4.0)/N4(dy20)
REJECT with named legs; N5 support-seat→NotInAnyRouteClip + selector excludes x=0.30; N6 built-C2 captured; N7
task_config-C2→0 geoms→BrokenSelector; audit A(no-pin) pass / B(off-clip z880.9)→AssertionError / C(legit) pass;
40 pin candidates. Multi-world: clip_geoms_at(C1)=5 at world_count∈{1,4} (single-world template).

## g6_live rollout RESULT (FM1, 2026-07-16, cuda:0, world_count=1, single-episode) — `g6_live_rollout_pin_result.json`

⚠ blocked-then-harness-patched: the source (d2) `_wire_c1_pin_from_recording` reads the prepared bank (no pin
fields) → crashes at init; g6_live monkeypatches the WIRING (source unchanged) to read pin data from the RAW npz.
That (d2) plumbing bug is a surfaced follow-up (F1 scaffold), NOT the authorizer (which is downstream at :1722).

- **FM-E (regression) VALIDATED LIVE**: pin FIRED at RL step 254 (onset 2544, seg 27); live onset seat
  [0.3509,0.1488,0.8275] = **dx 0.93mm / dy 1.18mm** vs C1 (both < bars); `authorizer_raise=null`,
  `position_match=0.0001mm`, `eq_active_readback=1`. The authorizer accepts the legit onset live; no regression.
- **piece ④ audit VALIDATED LIVE**: `audit_raise=null` — the fired pin is clip-anchored at episode-end.
- **FM1 (c1_retained reachable) VALIDATED**: `c1_retained_ever=true` — the pin makes c1_retained latch.
- ⚠ **G6 NOT reached** (`early_done=343`, `max_phase=3`, `g_latched_max=[1,1,1,1,0,0]`): the episode dropped at
  phase 3. This is the KNOWN coarse-substep grip-drop (comp5 ⑥ drops at the RL default 4 substeps; needs SUB10=10
  to hold the grip through the lift) — a rollout-fidelity matter, NOT the pin (which fired at 254 and held C1
  until the drop). ⇒ **do NOT claim "G6 reached"; claim "pin fires + c1_retained reachable, single-episode".**
  Full G6-latch demonstration needs SUB10 + the F1 scaffold fixes (per-episode fire, eq clear) = follow-up.

## FINAL gate status (this task = the AUTHORIZER leg)
[L-TRIAGE] L3 ✓ · [VERIFY] CC1-self + independent pre-check (PROCEED-WITH-FIXES, all addressed) ✓ · [RULE-CHECK]
ALL PASS ✓ · [CHANGE] 5-piece (py_compile/ruff clean, byte-neutral, SSOT untouched) ✓ · [RUN N1-N7] 14/14 ✓ ·
g6_live FM-E+FM1+audit live ✓. [层2/层5 L3 post-verify] = served by the independent pre-check (adversarial,
geometry/physics/SSOT axes) + N1-N7 + git-diff review. **AUTHORIZER = DONE + validated.** Permanent-wiring
scaffold (F1 a-d + (d2) recording-plumbing) + §19-signature-vs-§15.1 (→p5) = surfaced follow-ups.
