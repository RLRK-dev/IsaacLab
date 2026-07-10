---
doc_class: reference
---

# (a) policy_route_runner.py v2 — DESIGN PROPOSAL (CP-E prerequisite; NOT implemented)

For CP-E held-out rollouts on the 15-phase B2 abs policy. `policy_route_runner.py` is NON-locked. **2026-07-03.** Design only — implement + %12 review before CP-E.

## 1. obs 27D + affine[15] (localized, mirrors the ④ og pattern)
| line | now (13/25) | v2 (schema-aware) |
|---|---|---|
| :128 | `obs = np.zeros(25, …)` | `obs = np.zeros(12 + n_phases, …)` (n_phases from the loaded `abs_meta`) |
| :133 | `obs[12 + phase_idx] = 1.0` | unchanged mechanically (phase_idx ≤ 14 → idx ≤ 26; the wider obs covers it) |
| :327 | `build_actor_critic(25, 6, …)` | `build_actor_critic(obs_dim, 6, …)`, `obs_dim = 12 + n_phases` from `abs_meta["obs_dim"]` (bc_pretrain's is obs-dim-parametric — LOCKED, untouched) |
| :339 | `assert abs_affine.shape == (13, 6, 2)` | `assert abs_affine.shape == (n_phases, 6, 2)` (accept 15) |
| :881 | `np.zeros((0, 25), …)` | `np.zeros((0, 12 + n_phases), …)` |
| :265/:881 obs-parity | compares runner_obs(25) vs conv_obs(from dataset) | both must be `12+n_phases` (27 for B2) — the parity check widens automatically once :128/:881 are n_phases-aware |
- Source `n_phases`/`obs_dim` from the SAME place the OG gate does (④ pattern): `abs_meta = json.load(bc_dataset_abs_meta.json)`; `n_phases = affine.shape[0]`. Loud-echo the detected schema.

## 2. obs-parity is PRESERVED (verified this session)
The runner's `_live_seg_pos` (:117) uses `cable_pos[seated_body_row]` (pinned−28) for C1_SEAT/C1_PIN — the SAME convention the converter's `seated_seg=pinned−28` uses (D1 verified). So widening the obs to 27 keeps the runner's obs byte-consistent with the converter's training obs. The 15-schema GUIDE_C2 one-hot dim (9) is always 0 at rollout too (the route never enters it) — matching the dataset (D2). No obs-parity break.

## 3. ⚠ 15-phase schedule source (the real open question — needs %12/Rs design call at CP-E)
`convert_b2` emits **no `schedule.json`/`macro_schedule.json`** (they are per-single-demo; the multi-demo aggregate has none). The runner's open-loop **B0** replay path consumes a schedule (`phase_transitions`/`pin_event`/`grip_events`/`verdict_landmarks`). For CP-E:
- **The B1 policy-driven rollout** (what CP-E needs — deterministic actor-mean generating abs targets) does NOT need the demo schedule for the ACTIONS (the policy produces them). It DOES need the scripted grip-close + the C1 pin-fire events (those are scripted, not learned).
- **Proposed source options (record-only, %12/Rs to pick):**
  - **Opt-i (recommended): emit a per-representative-demo 15-phase schedule.** Run the existing single-demo `convert(..., --action-repr delta)` on ONE 15-phase demo (e.g. the nominal (0,0) or a train demo) → its `schedule.json` gives the 15-phase `pin_event`(frame)/`grip_events`/`phase_transitions`. The runner uses THAT for the scripted events. Additive, no locked-file touch, reuses the proven single-demo path. Caveat: the pin/grip FRAMES are that demo's; for other offsets they are ~invariant (the route's scripted cadence is offset-independent — the offset only shifts the grasp TARGET, not the phase schedule). Verify frame-invariance across a couple offsets.
  - **Opt-ii: the runner sources grip/pin events from the harness's own scripted logic** (the route already fires them by phase, not by demo-frame) — cleaner but a bigger runner refactor.
- **Recommend Opt-i** for CP-E (minimal, reuses `convert()` single-demo schedule); flag the frame-invariance check.

## 4. Also flagged (from the convert impl report, CP-E prereqs)
- LOCKED `og_offline_gate.py` PHASES13 import + 15-phase: **RESOLVED this session** (b) — og is 15-aware (④) + now empty-phase graceful; 13-phase byte-inert (NEW==OLD).
- The og gate's B2 run needs `--null-og <null policy's og_gate.json>` + `--carried-stops GUIDE_C2` (CARRIED_STOPS_PREREG) for the formal §3.4 null-beat; that is the CP-E OG-gate invocation, not a code change.

## Status
Design only. Implement (≈6 localized edits + the schedule-source Opt-i) → %12 review → CP-E rollouts (iff OG=GO).
