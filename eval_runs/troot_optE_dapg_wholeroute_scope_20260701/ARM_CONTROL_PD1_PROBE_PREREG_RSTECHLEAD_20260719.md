# P-D1 PREREG — arm-PD de-risk probe (design v1.5) 【v1.1 — FROZEN at this commit; runs after p5's declared-band readback】

| prereg ver | commit | note |
|---|---|---|
| v1.0 | `8ed56f65ea` | SUPERSEDED — froze pre-review; its 5-run batch = DIAGNOSTIC/NON-EVIDENCE (`fa1e786b46` disposition) |
| v1.1 | 〔this commit〕 | design v1.5 compliance: B1-strip / L-P0 REQUIRED-to-RUN / L-P2′+P-1/P-2 / **R3 stale-target primary negative (§12.1)** / A-1..A-6 (§12.2) with declared bands |

- **Author:** RS-TECH-LEAD (w2:p4). **Status per the review's P0-2 taxonomy:** production impl CLOSED / probe scaffolding BUILT-UNLANDED (v0.5) / smokes+diagnostic batch EXECUTED (non-evidence) / probe evidence NONE until this v1.1's runs / authority CLOSED.
- **Design:** `ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md` **v1.5** (bank `a584be8545`, version-table fixes `c951a072d7`+`084064778d`; chain: v1.1 @4 / v1.2 Option B / v1.3 route-start re-pose / v1.4 review-v1 compliance + B1-strip / v1.5 review-v2 residuals + §12). **Findings:** `b9eaaf9d93`, `c1da5dcf54`; **disposition + diagnostic batch:** `fa1e786b46`. **Brief:** `1ee8be5c9e`. **Rs reviews:** v1 + v2 (`~/Downloads/PLAN_STATUS_review{,_v2}_2026-07-19.md`).
- **PD-write surface (v1.5-① s1-s4):** s1 `apply_recorded_arm_ff` ctrl write (FF actual path = THE probe drive site) / s2 `newton_route_env` RL-path branch (present, NOT exercised in FF — S-1 scope) / s3 route-start re-pose / s4 harness M-4 sync.
- **#3 mechanism (implemented, smoke-validated):** flag-gated B-class boundary init in `_reset_worlds` — arm q := recording frame-0 exact values + qd 0 + ctrl target-sync (M-4), gripper-OPEN ∧ not-grasping guard asserts, loud + `route_start_repose_count` in the summary. Smoke-4: fires once/episode, **err[0] = 4e-5 rad** (the repurposed L-P4 "no haul" predicate at smoke level).
- **Neutralization mechanism (v1.4-③): B1-STRIP** — the 12 imported ur5e.xml arm actuators are removed at the proto (vendor values captured + numerically cross-checked first); census asserts exact nu (16 PD / 4 L-P0), imported set structurally ABSENT. Smoke-5/6 PASS. No dynamic force≡0 test needed (that requirement attaches to the B2 fallback only).
- **Purpose (pivotal unknown, design §5):** does the MuJoCo arm PD (vendor gains, ±150/±28 N·m caps) track the recorded FF whole-route within the frozen bars, with cable+grasp load, at the trainer cadence @4?

## 1. Substrate (pinned)

- Worktree branch `probe/pd1-arm-pd` (base `0f39f7b598`), **final code sha = `a217086822`** (v0.2 `ab834ef4ab` FF-ctrl / v0.3 `5084712d2c` re-pose+body_q / v0.4 `3b7251029c` B1-strip / v0.5 `a217086822` **stale-R3 + A-suite**). Probe-only; NOT landed; landing = L3 chain + Rs sign-off (design §9). Path-freeze scope note (review ⑧): the probe touches committed files only; the S-1 migration path freeze will enumerate committed / WIP / excluded separately.
- Env: `NewtonRouteEnv` wc=1, FF whole-route, `route_c1_pin=True` (real pin), `g1_scene_align=True`, `route_c2_scene=True`, `INIT_XY_NOISE=0`, cadence RL@4 (`RL_SIM_SUBSTEPS=4`, no knob — 訂正#1).
- Recording: `w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz` (nominal; harness pins sha256 into provenance).
- Venv `/home/rlrk/env_isaaclab7` (exact `sys.prefix` bar) / `CUDA_VISIBLE_DEVICES=0` / `--device cuda:0` / MUJOCO_GL=egl / fresh-outbox + device + source-closure hard bars (gonow lineage, all inherited in `armpd_probe.py`).

## 2. Frozen bars (design §3.2 v0 — scored OFFLINE against these; ⛔ no post-hoc bar moves: a change = declared diff + rerun)

| leg | bar |
|---|---|
| L-P1 per-joint quasi-static | ≤ 2 mrad |
| L-P1 per-joint transient | ≤ 5 mrad |
| L-P1 EE (wrist flange) quasi-static / transient | ≤ 1.5 mm / ≤ 3 mm |
| L-P3 effort saturation (per joint, share of frames at cap) | WARN > 1% / FAIL > 5% |
| TRIP (M-6, informational in probe) | 15 mrad |
| **R3 stale-target negative control (v1.5 §12.1 PRIMARY; supersedes L-P5′):** | scoring stream = **intended (recording): \|q − rec[t]\| per frame** (⛔ NEVER vs the frozen ctrl — vacuous-PASS trap, demonstrated in smoke-7: \|q−ctrl\| 0.007 vs \|q−intended\| 0.758). Two legs: (i) **calibration** — measured curve matches the precomputed \|rec[0]−rec[t]\| per joint within **band = 0.06 rad + 5%·predicted** (declared; PD hold sag ≈ τ_g/kp ≲ 0.04 rad + noise; smoke-7 observed deviation 8e-4) — band exceeded ⇒ **instrument INVALID** (not probe FAIL); (ii) **fail-ability** — the measured error must exceed ≥1 L-P1 bar (rad-scale ≫ mrad bars = structurally guaranteed, pipeline must FLAG it). ×0.1 = **R4 exploratory** (non-gating). |
| L-P6 census | PASS in every run (B1-strip: PD = nu 16, 12 live design servos, imported ABSENT; L-P0 = nu 4; baseline = N/A) |
| M-6 divergence dwell (measured leg, NOT enforced in the probe) | report per-joint counts of ≥N_DIV=48-frame dwells above the transient bar (v1.4-⑥ semantics); feeds the S-1 `ARM_DIVERGENCE_BAR_RAD` freeze |

- **Phase split (operationalized, frozen):** quasi-static window = RL steps ∈ [g3_step, done/end] of THAT run's `per_step` (seat/route window); transient = all other frames (incl. activation/ramp). Declared, not gerrymandered post-hoc.
- **L-P2 (v1.4 re-scope): parity vs the CONTAMINATED baseline R0 = characterization ONLY (not acceptance).**
  **L-P2′ acceptance (p5 RATIFIED 11:26 + 2 refinements): parity vs the CLEAN-substrate kinematic reference R0b** — PD (R1) must reproduce the predicate chain that the clean kinematic playback itself produces (same-substrate apples-to-apples: g3/pin/first-cause class as in R0b, shifts declared). Separation: "PD can't track the stream" = L-P1/L-P3 (vs own ctrl stream); "the chain requires the artifact" = L-P0; L-P2′ = PD ≈ clean-kinematic.
  - **P-1 (ratified refinement):** ADD a REPORTED (bar-less) R1-vs-R0b **continuous divergence** leg (EE + cable proxy per frame) — guards against parity-in-failure degeneration when R0b's chain itself collapses (two failure modes could otherwise "match" vacuously).
  - **P-2 (ratified refinement):** an EMPTY quasi-static window (g3 never fires) is reported **N/A — never PASS** (an unreachable window must not satisfy a bar vacuously).
- **L-P0 magnitude (v1.4-④ REQUIRED):** R0-vs-R0b same-seed divergence under the B1 mechanism: per-frame arm |Δq|, predicate deltas, parity table — the tug-of-war component alone (Rs caveat-scale material, design §7-5; evidence-grade with verification legs + the video leg).
- **L-P4 (repurposed per v1.3):** verify |q−ctrl| stays within the transient bar **from frame 0** after the route-start teleport+sync (no physical haul) — scored on R1. M-5 ramp now applies only to residual discontinuities; **R2 (ramp-on) is retained as a mechanism no-regression leg**: with a synced start the ramp should be ≈identity, so R2 ≈ R1 is EXPECTED — a large R2-vs-R1 divergence = LOUD anomaly (reported, not barred).

## 3. Run matrix (v1.5-② 6 runs, frozen order; each: fresh outbox leaf, `--episode-steps 900`, set -e fail-closed sequencing, launched from the worktree)

| run | tag | flags | substrate | pass-role (decision での役割) |
|---|---|---|---|---|
| R0 | `r0v11_kin` | (none) | banked AS-IS (imported tug present, kinematic) | characterization only (contaminated reference; L-P2 non-acceptance) |
| R0b | `r0v11_lp0` | `--neutralize-only` | clean (B1-strip), kinematic | **L-P0 REQUIRED-to-RUN** impact assessment (gates banked-evidence reuse, NOT a probe pass condition) + the L-P2′ clean reference |
| R1 | `r1v11_pd` | `--arm-pd` | clean, PD drive | **primary**: L-P1/L-P3 bars (vs own ctrl≡intended) + L-P4 no-haul + L-P2′ parity vs R0b + M-6 dwell leg |
| R2 | `r2v11_pd_ramp` | `--arm-pd --ramp-frames 120` | clean, PD + M-5 ramp | mechanism no-regression (≈R1 expected; large delta = LOUD anomaly, reported) |
| R3 | `r3v11_stale` | `--arm-pd --neg-stale` | clean, PD, ctrl frozen at route-start | **§12.1 PRIMARY negative control**: instrument calibration + fail-ability (scored vs intended stream) |
| R4 | `r4v11_gains01` | `--arm-pd --gains-scale 0.1` | clean, PD ×0.1 gains | exploratory (non-gating gain-sensitivity reference) |

Outboxes: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pd1_probe_20260719/<tag>/`; run logs to the parent dir. (New v1.1 tags — the v1.0 diagnostic leaves stay untouched as NON-EVIDENCE records.)

### Declared bands (v1.5 §12.2 — p5 readback target)

| item | declared value | basis |
|---|---|---|
| §12.1 calibration band | 0.06 rad + 5%·predicted, per joint | PD hold sag ≈ τ_g/kp ≲ 0.04 rad (shoulder_lift worst) + noise margin; smoke-7 observed 8e-4 |
| A-4 ε_pen | **3 mm** (min active-contact dist ≥ −0.003 m on the first post-re-pose frame) | banked pad-compliance penetration ≈ 1.1 mm scale; 3 mm = loud-breach bound. Implemented form = GLOBAL min over active contacts (conservative superset of arm-involved; mujoco_warp `nacon` prefix) |
| A-4 cable Δv band | first-frame `cable_vmax` ≤ max(2× R0b same-frame value, 0.01) | comparative per §12.2 (R0b 同 frame 比、2× 宣言 + noise floor); smoke scale ≈ 2e-4 |
| M-6 dwell report | N_DIV = 48 frames, bar candidate = 15 mrad (transient ×3) | v1.4-⑥; reported counts only (not enforced in the probe) |
| L-P1 scoring stream (normal PD runs) | `\|q − ctrl\|` with an analysis assert `max\|ctrl − intended\| ≤ 1e-9` (wiring cross-check) | R3 alone is scored vs intended (§12.1 condition) |

## 4. Measurement / artifacts (per run, harness-emitted)

- `summary_<tag>.json` (provenance + effective config + predicates + quick tracking) / `per_step_<tag>.json` / `armpd_frames_<tag>.npz` (per-physics-frame arm q/qd/ctrl + per-RL-step body_q for the offline video replay) / `COMPLETE.ok` (integrity-verified only).
- Offline analysis (post-run script, committed with results): L-P1 bars (incl. EE via mj FK on q/ctrl — **wrist flange**, labeled), L-P3 effort = clip(ke·(ctrl−q) − kd·q̇, ±cap) (exact for the affine servo), L-P0/L-P2 tables, L-P4 transition metrics.
- **Video leg (mandatory, design §5):** PD run offline replay render from the body_q log → Rs (~/Downloads), alongside the Rs motion standard `p2r_c11_route.mp4`. Physical-validity judgment = Rs (human-GT).

## 5. Decision tree (design §5, frozen)

- L-P1/L-P3 bars PASS (vs own ctrl stream) ∧ R3 calibration + fail-ability hold (§12.1) ∧ L-P6 PASS ∧ L-P2′ parity vs R0b → probe PASS → p5 bar-freeze finalization → §6 rollout (S-1; **landing still gated by #18-first R-SEQ + L3 chain + Rs**).
- FAIL(tracking) → gains sensitivity frame §8-4 (×0.5/×2.0, effort caps untouched) → re-run w/ declared diff.
- FAIL(saturation) → re-trajectory/speed-profile chunk = SEPARATE (Rs 報告, design §5 分岐).
- **R0b chain ≠ banked chain (L-P0 large, as the diagnostic suggested)** → that is an L-P0 RESULT, not a probe failure: reported Rs-visible per v1.4 §7-5 (banked-caveat scale + decision-critical contrast rerun scope = Rs).

## 6. Sequencing / concur

- **R-SEQ concur (design §6):** %12 concurs — #18 lands first on the kinematic basis; P-D1 runs now in parallel (read-only branch). No reverse-order request.
- Probe result dispatch: p5 (bar freeze + verdict is p5's §9 gate) + p6 relay at bank.
