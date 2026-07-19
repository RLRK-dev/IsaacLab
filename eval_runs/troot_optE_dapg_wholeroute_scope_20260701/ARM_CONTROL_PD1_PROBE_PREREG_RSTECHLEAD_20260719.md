# P-D1 PREREG — arm-PD de-risk probe (design v1.3) 【FROZEN at this commit; runs strictly after】

- **Author:** RS-TECH-LEAD (w2:p4). **Status:** v1.0 FROZEN — correction #3 resolved (route-start re-pose, design v1.3); the run matrix, bars, and code shas below are final. Any change after this commit = declared diff + rerun.
- **Design:** `ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md` **v1.3** (bank `054ccf139a`; v1.1 cadence 訂正#1 = P-D1 @4; v1.2 訂正#2 = Option B; v1.3 訂正#3 = route-start re-pose). **Findings:** `b9eaaf9d93` (imported actuators / tug-of-war), `c1da5dcf54` (start pose). **Brief:** `1ee8be5c9e`.
- **#3 mechanism (implemented, smoke-validated):** flag-gated B-class boundary init in `_reset_worlds` — arm q := recording frame-0 exact values + qd 0 + ctrl target-sync (M-4), gripper-OPEN ∧ not-grasping guard asserts, loud + `route_start_repose_count` in the summary. Smoke-4: fires once/episode, **err[0] = 4e-5 rad** (teleport+sync holds from frame 0 = the repurposed L-P4 "no haul" predicate at smoke level).
- **Purpose (pivotal unknown, design §5):** does the MuJoCo arm PD (vendor gains, ±150/±28 N·m caps) track the recorded FF whole-route within the frozen bars, with cable+grasp load, at the trainer cadence @4?

## 1. Substrate (pinned)

- Worktree branch `probe/pd1-arm-pd` (base `0f39f7b598`), **final code sha = `5084712d2c`** (v0.2 = `ab834ef4ab` + v0.3 route-start re-pose + body_q logging). Probe-only; NOT landed; landing = L3 chain + Rs sign-off (design §9).
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
| L-P5 negative control (gains ×0.1) | **must FAIL ≥1 L-P1 bar** — else the instrument is non-discriminating ⇒ probe INVALID |
| L-P6 census | PASS in every run (mode-appropriate: PD = inert 12 + live 12; L-P0 = inert 12 + live 0; baseline = N/A) |

- **Phase split (operationalized, frozen):** quasi-static window = RL steps ∈ [g3_step, done/end] of THAT run's `per_step` (seat/route window); transient = all other frames (incl. activation/ramp). Declared, not gerrymandered post-hoc.
- **L-P2 parity (predicate outcomes vs R0, not frame equality):** g3 reached (y/n) / pin fired (y/n) / first-cause drop class (A/B/C/explosion/none). Step/frame shifts = **declared deltas** (design §5 L-P2).
- **L-P0 magnitude:** R0-vs-R0b same-seed divergence: per-frame arm |Δq|, cable predicate deltas, per_step parity table — the tug-of-war component alone (Rs caveat-scale material, design §7-5).
- **L-P4 (repurposed per v1.3):** verify |q−ctrl| stays within the transient bar **from frame 0** after the route-start teleport+sync (no physical haul) — scored on R1. M-5 ramp now applies only to residual discontinuities; **R2 (ramp-on) is retained as a mechanism no-regression leg**: with a synced start the ramp should be ≈identity, so R2 ≈ R1 is EXPECTED — a large R2-vs-R1 divergence = LOUD anomaly (reported, not barred).

## 3. Run matrix (5 runs, frozen order; each: fresh outbox leaf, `--episode-steps 900`, set -e fail-closed sequencing, launched from the worktree)

| run | tag | flags |
|---|---|---|
| R0 baseline (banked substrate AS-IS) | `r0_kin` | (none) |
| R0b L-P0 (neutralize-only, kinematic) | `r0b_lp0` | `--neutralize-only` |
| R1 PD | `r1_pd` | `--arm-pd` |
| R2 PD + ramp (mechanism no-regression; expected ≈ R1) | `r2_pd_ramp` | `--arm-pd --ramp-frames 120` |
| R3 PD negative control | `r3_pd_neg` | `--arm-pd --gains-scale 0.1` |

Outboxes: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pd1_probe_20260719/<tag>/`; run logs to the parent dir.

## 4. Measurement / artifacts (per run, harness-emitted)

- `summary_<tag>.json` (provenance + effective config + predicates + quick tracking) / `per_step_<tag>.json` / `armpd_frames_<tag>.npz` (per-physics-frame arm q/qd/ctrl + per-RL-step body_q for the offline video replay) / `COMPLETE.ok` (integrity-verified only).
- Offline analysis (post-run script, committed with results): L-P1 bars (incl. EE via mj FK on q/ctrl — **wrist flange**, labeled), L-P3 effort = clip(ke·(ctrl−q) − kd·q̇, ±cap) (exact for the affine servo), L-P0/L-P2 tables, L-P4 transition metrics.
- **Video leg (mandatory, design §5):** PD run offline replay render from the body_q log → Rs (~/Downloads), alongside the Rs motion standard `p2r_c11_route.mp4`. Physical-validity judgment = Rs (human-GT).

## 5. Decision tree (design §5, frozen)

- ALL bars PASS ∧ L-P5 FAILs ∧ L-P2 parity → probe PASS → p5 bar-freeze finalization → §6 rollout (S-1; **landing still gated by #18-first R-SEQ + L3 chain + Rs**).
- FAIL(tracking) → gains sensitivity frame §8-4 (×0.5/×2.0, effort caps untouched) → re-run w/ declared diff.
- FAIL(saturation) → re-trajectory/speed-profile chunk = SEPARATE (Rs 報告, design §5 分岐).

## 6. Sequencing / concur

- **R-SEQ concur (design §6):** %12 concurs — #18 lands first on the kinematic basis; P-D1 runs now in parallel (read-only branch). No reverse-order request.
- Probe result dispatch: p5 (bar freeze + verdict is p5's §9 gate) + p6 relay at bank.
