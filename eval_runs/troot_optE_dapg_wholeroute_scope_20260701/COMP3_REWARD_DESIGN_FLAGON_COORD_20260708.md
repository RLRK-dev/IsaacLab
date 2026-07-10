---
doc_class: design-surface
---

# /reward-design (SCOPED) — comp3 flag-ON delta: predicate reachability under live grip + R6 obs table — %11 COORD

**node:** T-ROOT-optE-route-dapg-C1C2-P2-routeexec — comp3 Stage-B design-gate, gate (3).
**trigger:** %12 06:57 — /reward-design SCOPED to the flag-ON delta (predicate reachability under live grip + R6 obs table). PLANNING (no-GPU, paper).
**⛔ SCOPE:** comp3 does **NOT change the reward function or success condition** — both are env-core-owned and UNCHANGED (`_compute_rewards_dones_batch` :984; strict_v2 = c1_retained ∧ c2_seat). flag-ON ACTIVATES live grip (env-wiring). This scoped gate checks: (a) does live grip change PREDICATE REACHABILITY? (b) the R6 obs[7]/[15] change vs §運用21 obs-reward integrity. **The reward's inputs are read from PHYSICS state (cable_pos), NOT obs — verified below.**

---

## §運用21 obs-reward integrity check (the load-bearing finding)
`_compute_rewards_dones_batch` (:984-1071) reads **cable_pos = bq[cable_bodies]** (physics, :1001) and derives every reward/predicate input from it: `_seat_metrics(cable_pos)` c2_seat (:1014), `_c1_retention_m(cable_pos)` z_c1/flank (:1015), `_c2_seated_honest(cable_pos)` (:1022), G1-G6 latches (:1066). **The reward NEVER reads obs_np.** obs[7]/[15] (r_finger/l_finger, :930/:933) feed the POLICY, not the reward. ⇒ **the R6 obs change has ZERO reward dependency** — §運用21 satisfied (reward inputs = physics, unaffected by the obs-side R6 fix).

## Artifact 1: Reachability table (flag-ON delta — reward UNCHANGED)
| predicate (env-core) | formula | gate | reachable flag-OFF? | reachable flag-ON? | dead zone? |
|---|---|---|---|---|---|
| c1_retained | z_c1<0.840 ∧ flank<0.840 [m] (:1018, rc.C1_RETAINED_LOW_WALL_TOP_M) | cable gripped+carried | **NO live** (fingers pinned OPEN :779; cable not gripped → offline recorded-state only, env-core ⑨a′=25/81 ceiling) | **YES** (servo grips → cable carried → z_c1 reflects carried cable) | flag-OFF: N/A-inert; **flag-ON: none** |
| c2_seat | seat_metrics wall-dist≤0.5mm spacer-excl (:1014, DoD⑤) | cable dragged to C2 groove | NO live (no carry) | YES (carried cable dragged→seats) | flag-ON: none |
| G1-G6 latch | ordered monotonic (:1066; k>0 requires k-1) | physical grasp→lift→route→seat | NO live | YES (real carry fires latches in order) | none |
⭐ **flag-ON ENABLES reachability that flag-OFF could not** (the live legs ⑨b/⑥ were undischargeable with fingers pinned OPEN — verdict NHA A0). No dead zone INTRODUCED; the reward function/thresholds are unchanged. **Reachability is CONDITIONAL on the live grip HOLDING** (SRG-validated on build_scene; G1 validates on the env) — that is the G1 gate, NOT a reward-design deadlock.

## Artifact 2: Causal Gate DAG (flag-ON)
```
action(6D residual) -> project -> IK arm pose (:791 arm-only) + grip servo (recorded staircase :967) [FLAG-ON: grip node ACTIVE]
   -> cable GRIPPED + CARRIED (physics) -> cable_pos -> z_c1/c2_seat/held_z (:1001-1022)
   -> G1(grasp) --[latch]--> G2(lift held_z<rest+DROP_LIFT :1042) --> ... --> G5(c2_seat<T_GROOVE :1060) --> G6(sustain)
   -> reward
```
- Every `--[latch]-->` is env-core-owned (unchanged, ordered-monotonic). **flag-OFF: the grip node is INERT (cable not carried) → G1 never fires live → the whole chain is dead-live (offline-only).** flag-ON makes the grip node ACTIVE → the chain completes on REAL physics. **No NEW gate/deadlock introduced by comp3** (it removes the inert-grip block, it does not add a gate).

## Artifact 3: Ground-truth values (predicate thresholds UNCHANGED; flag-ON = whether carried)
| state | z_c1 [m] | c2_seat | grip | c1_retained | c2 fire | note |
|---|---|---|---|---|---|---|
| P0 (reset, OPEN) | ~0.809 (cable on table) | far | open | (n/a pre-grasp) | no | route starts |
| grasped (flag-ON) | carried (SRG: z-drop ≤7.4mm → z_c1 stays <0.840) | far | closed | YES | no | G1 latch |
| seated (flag-ON) | <0.840 | ≤0.5mm groove | closed | YES | YES | strict_v2 both-leg |
| flag-OFF (any) | 0.809 static / recorded | recorded | forced-OPEN | offline-only | offline | inert grip |
- thresholds (0.840, T_GROOVE, 0.5mm) = env-core SSOT, UNCHANGED. flag-ON changes whether the cable is physically carried, so whether z_c1/c2_seat reflect a REAL carried cable (SRG: z-drop within margins → z_c1<0.840 holds when carried).

## Artifact 4: Episode trace (flag-ON, recorded-replay)
Step 0: reset OPEN (route step-0). Step k1: recorded ee_pos descends + grip staircase closes (0.667 cage90→0.7407) → cable GRIPPED → G1 latch. Step k2-k3: lift+route drag, cable carried (SRG cage holds) → z_c1<0.840 sustained. Step k4-k5: C2 approach → c2_seat drops → G5 fires → G6 sustain → strict_v2. **No deadlock** — the recorded schedule drives the arm+grip; the reward latches fire on the physical carry (which SRG validated holds; G1 confirms on the env substrate). ⚠ intra-window close-on-transient (pre-check ISSUE 3) → G1 close-frame zoom.

## R6 obs table (obs[7]/[15] — the ONLY obs change; no reward dependency)
| obs dim | flag-OFF (current) | flag-ON (comp3 R6) | reward reads it? |
|---|---|---|---|
| obs[7] r_finger (:930) | `_per_world_fk_jq` FK-side (forced-OPEN :779 — TRUTHFUL flag-OFF since fingers ARE open) | **physics joint_q readback** (real servo-driven opening — else FK-side would LIE flag-ON) | **NO** (policy-only) |
| obs[15] l_finger (:933) | same FK-side | same physics readback | **NO** |
- R6 fix makes the POLICY's finger-observation truthful under flag-ON; the REWARD is unaffected (reads cable physics). L4 unit asserts the flag-ON obs source (physics, not FK).

## [REWARD DESIGN GATE]
- Reachability: **PASS** (flag-ON ENABLES the offline-only predicates; no dead zone introduced; reward unchanged).
- Causal DAG: **PASS** (no new gate/deadlock; flag-ON removes the inert-grip block).
- Ground-truth: **PASS** (thresholds unchanged; SRG-validated the carry keeps z_c1<0.840).
- Episode trace: **PASS** (recorded-replay drives arm+grip; latches fire on real carry; close-frame zoom carried).
- §運用21 obs-reward: **PASS** (reward reads physics cable_pos, NOT obs[7]/[15]; R6 = policy-observation fidelity only).
- **GATE = PASS** (SCOPED: comp3 does not change the reward/success; flag-ON activates reachability that was inert under flag-OFF; R6 obs change has no reward dependency). ⚠ reachability is CONDITIONAL on the live grip holding = the G1 validation (not a reward deadlock).

---
*%11 COORD (w2:p3) 2026-07-10. /reward-design SCOPED to comp3 flag-ON delta. No-GPU paper. GATE=PASS. Reward/success env-core-owned UNCHANGED. Gate (3) of 3. → %12 re-gate ping.*
