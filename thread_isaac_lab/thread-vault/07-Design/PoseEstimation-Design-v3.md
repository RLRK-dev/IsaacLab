---
status_ledger: 00-DESIGN-STATUS-LEDGER.md  # authoritative success/failure status SSOT
title: Pose Estimation Design v3 — obs Replacement via Wrist RGB-D + Joint State (post-debate revision)
created: "2026-04-25T06:00:00+09:00"
updated: "2026-04-25T07:10:00+09:00"
status: "Proposal / Parked Design Stock — v2 debate PASS_WITH_REVISIONS 結果を反映"
owner: "CC#4 / Pose Estimation Research"
supersedes: "[[PoseEstimation-Design-v2]]"
debate_record: "5-CC Debate 2026-04-25 (CC2 general / CC3 infra / CC4 past-failure / CC5 R6 / CC6 NHA) — 5 CRITICAL + 14 HIGH accepted"
rs_decision: "Option X2 approved 2026-04-25 — adopt v2 stock + v3 revision round"
tags:
  - design
  - vision
  - pose-estimation
  - cable
  - clip
  - msa-obs
  - sim-to-real-prep
  - parked-vision-stack
  - post-debate
---

# Pose Estimation Design v3

> **⚠ PARTIAL SUPERSEDE (parent base) — renewal batch B, 2026-07-11 (banner-only; content edit-frozen):** this is the **parent base** of the pose-estimation head stock (`00-DESIGN-STATUS-LEDGER.md:52` = 🔁 **SUPERSEDED** → v3.1, v3.2). It is superseded **only where v3.1/v3.2 patch it**; per v3.2 frontmatter *"v3 remains parent"*, unpatched sections remain **normative** as the base of the composite head. Read as part of the head stack — **open v3 + v3.1 + v3.2 together** (v3.2 §1.1). Current head: `[[PoseEstimation-Design-v3.2]]` (`:50`, PARKED/unvalidated). Status SSOT = `00-DESIGN-STATUS-LEDGER.md`.

## 0. Executive decision

### 0.1 Recommendation (revised from v2)

Adopt **Option C-2R: Routing-conditioned Hybrid pose estimation** as target design, but **scope narrowed to AC-only for MVP-0A~3**. IC / AR / Grip integrations are explicitly **deferred** pending a prerequisite SSOT consolidation of per-skill observation contracts (see §2.5).

Stack unchanged from v2 at the stage level, but revised at the contract and fallback level:

1. **Stage 0 — Kinematic prior and ROI proposal** (Warp-kernel mandatory, per-world isolated)
2. **Stage 1 — Light segmentation + instance-aware clip heads + auxiliary validity/occlusion heads** (measured benchmark gates OQ-1 approval)
3. **Stage 2 — Analytic 3D reconstruction with binary (not NN-soft) point weights** for Stage 3 residual (R6 preservation)
4. **Stage 3 — Surrogate-assisted constrained refinement** with **hard idempotent projection operator** + arc-length monotonicity (not image-space monotonicity)
5. **Stage 4 — Probabilistic temporal filter and fallback gate** with physical-proxy confidence + augmented obs contract (state bits + confidence to policy) + explicit FAIL_CLOSED → `dones=True, timeouts=False`

### 0.2 Implementation stance (unchanged from v2)

Remain **parked** until Vision Stack un-park or sim-to-real preparation is explicitly prioritized. Current sim-only Phase 5 path is sufficient with GT observations.

### 0.3 MVP recommendation (revised with AC-only scoping)

| MVP | Scope | Exit gate |
| --- | --- | --- |
| MVP-0A | Stage 0 + Stage 1 segmentation、wrist_L only、AC environment only、offline replay (no cuda:0 sim slot) | Cable mask mIoU > 0.8、5-clip mask mIoU > 0.75、ROI recall > 0.95、aux depth-valid AUROC > 0.85、aux occlusion AUROC > 0.80 |
| MVP-0B | Add wrist_R + self-occlusion masking | Two-view fusion improves target visibility > 10pp vs one-camera、false-positive on gripper/body < 5% pixel ratio |
| MVP-1 | Stage 2 point clouds、robust filtering | cable > 200 valid weighted points in ≥ 90% of frames、each visible clip > 50 points |
| MVP-2A | Stage 3a surrogate warm-start **only**、no policy touch | Surrogate proposal within projection convergence basin for ≥ 90% of frames (basin: 10 LM iters reduce residual ≥ 90%) |
| MVP-2B | Stage 3 hard-projection + robust refinement | cable target seg position error < 5 mm、orientation error < 0.05 rad on AC offline frames |
| MVP-2C | Stage 4 confidence/fallback state machine | ACCEPT/PREDICT/FALLBACK/FAIL_CLOSED labels correlate with measured residuals (> 0.7 rank correlation) |
| MVP-3 (AC-only) | Replace AC obs[16:30] in env、recompute error obs[30:42] from estimator、augmented obs contract (42D → 47D: 4 state bits + 1 confidence scalar) | AC success ≥ 90% of GT baseline over 100 eval episodes |
| MVP-4 | **Deferred** pending §2.5 SSOT consolidation for IC/AR/Grip | — |

**Do not begin MVP-0 implementation** without Rs authorization (OQ-1 + OQ-2 + OQ-3). The staged boundary is Rs decision, not a CC autonomous trigger.

### 0.4 Key v3 changes from v2 (debate response summary)

| v2 claim / under-spec | v3 resolution | Source CHALLENGE |
| --- | --- | --- |
| "13D obs[16:29]" | **14D obs[16:30]** (Python-slice correct) + per-skill contract table | CC2-1 / CC3-8 |
| Stage 1 "10-15 ms" unmeasured | Explicit measured-benchmark gate pre-OQ-1 + memory budget table | CC3-1 / CC3-2 |
| DD-PINN primary warm-start | "Surrogate candidate" with analytic-tangent fallback + dataset cost scope | CC3-3 |
| "Preserves 42D contract" uniform | Per-skill semantic contract table: AC/AR/Grip=42D, IC=45D groove-relative (deferred) | CC4-1 (verified in env) |
| FAIL_CLOSED obs/termination behavior | Explicit rule: dones=True, timeouts=False, obs[16:30]=last-accepted or zero-flag, error block propagation defined | CC2-4 / CC4-2 |
| "constraint projection" undefined | Hard idempotent projection operator (§5.4) | CC2-2 / CC5-1 |
| Confidence score unweighted | Per-term units + Σw=1 normalization + physical proxies replace NN mask_conf in gate | CC2-3 / CC5-9 |
| Stage 3a "3-5 ms" | Split: surrogate ~3-5 ms / projection+refine ~15-30 ms measured-TBD | CC2-5 / CC3-7 |
| OQ-3 parallel to Phase 5-1 | Offline data-replay default (0 cuda:0 slot) | CC3-5 |
| Stage 0 scipy path | Warp kernel **mandatory**, scipy-loop migration prereq | CC3-4 |
| `prev_cable_state` semantics | Per-world isolation contract + reset rule | CC4-4 |
| MVP-3 finetune vs GT ckpt | Rollback rule (value_loss >3× baseline → fresh start) | CC4-5 |
| Stage 4 regime anonymity | Augmented obs (state bits + confidence) — contract break disclosed | CC5-2 / CC5-8 |
| FALLBACK_NOMINAL_CLIP | **Forbidden under DR** | CC5-3 |
| NN-soft point weights in Stage 3 | **Binary** weights (threshold > 0.5) for Stage 3 residual、NN confidence → Stage 4 only | CC5-4 / CC5-9 |
| Smoothing IIR | Restricted to high-confidence OR Cosserat propagation、forbidden at alpha < 1.0 during low-confidence | CC5-5 |
| Monotonicity (image space) | Arc-length monotonicity (Cosserat physical law) | CC5-7 |
| obs[30:42] R6 exposure | Disclosed in §6.2 + regime-aware training requirement | CC5-10 |
| AR penalty bias replay | §10 risk register + MVP-2C bias measurement gate | CC4-3 |
| BC demo mismatch | Pre-finetune demo re-collection or BC loss equivalence | CC4-8 |
| Quat convention | Explicit unit test: match Newton body_q byte-for-byte | CC4-6 |
| Kinematic trick fallback | §10 prohibition + integration test grep | CC4-7 |

---

## 1. Design goal

### 1.1 Problem statement (revised, per-skill accurate)

The MSA observation contract differs per-skill. Replacement target depends on the skill. Below is the **verified per-skill obs layout** (v3 addition, was implicitly wrong in v2):

#### AC / AR / Grip (42D common, per `thread-vault/07-Design/RL-Routing-Design.md` §4)

| Slice (inclusive) | Python slice | Dim | Meaning | Current source |
| --- | --- | --- | --- | --- |
| 16..18 | `obs[16:19]` | 3 | target cable seg pos XYZ | Newton `state.body_q[target_seg_idx][:3]` |
| 19..22 | `obs[19:23]` | 4 | target cable seg quat (xyzw, w≥0) | Newton `state.body_q[target_seg_idx][3:7]` |
| 23..25 | `obs[23:26]` | 3 | current target clip pos XYZ | `task_config.py` CLIP\_{1..5}\_POS + routing index |
| 26..29 | `obs[26:30]` | 4 | current target clip quat | routing + fixed clip quat |
| **Total** | `obs[16:30]` | **14D** | cable+clip target pose block | — |
| 30..32 | `obs[30:33]` | 3 | R axis-angle orientation error | derived from hand_R_quat + seg_quat |
| 33..35 | `obs[33:36]` | 3 | R position error | derived from hand_R_clamp_pos + seg_pos |
| 36..38 | `obs[36:39]` | 3 | L axis-angle orientation error | derived from hand_L_quat + seg_quat |
| 39..41 | `obs[39:42]` | 3 | L position error | derived from hand_L_clamp_pos + seg_pos |
| **Error block** | `obs[30:42]` | **12D** | — | — |

**Total pose-dependent region**: `obs[16:42]` = 26D (14D pose + 12D error). This is what the estimator must replace / drive for AC / AR / Grip.

#### IC — different layout! (**45D**, groove-relative、verified from `newton_insert_clip_env.py:1165-1181`)

| Slice (inclusive) | Python slice | Dim | Meaning |
| --- | --- | --- | --- |
| 0..2 | `obs[0:3]` | 3 | R clamp pos **relative to groove** |
| 3..6 | `obs[3:7]` | 4 | R clamp quat |
| 7..9 | `obs[7:10]` | 3 | L clamp pos relative to groove |
| 10..13 | `obs[10:14]` | 4 | L clamp quat |
| 14..16 | `obs[14:17]` | 3 | cable-groove position error |
| 17..19 | `obs[17:20]` | 3 | cable-groove axis-angle orientation error |
| 20 | `obs[20:21]` | 1 | cable-groove distance (scalar) |
| 21..41 | `obs[21:42]` | 21 | cable shape (7 seg × 3D) relative to groove |
| 42..44 | `obs[42:45]` | 3 | cable linear velocity |
| **Total** | `obs[0:45]` | **45D** | — |

**IC has no obs[16:30] pose block**. IC already uses **groove-relative error signals** computed from sim GT. Estimator integration in IC is **architecturally different** — it needs to estimate the 21D shape + 3D pos error + 3D ori error + 1D distance, not a 14D absolute pose. **MVP-4 (IC expansion) is therefore deferred until an SSOT decision about whether to unify IC with 42D common spec or to implement IC-specific estimator head**.

**Scope impact:** v3 MVP-0A~3 apply to AC (42D) only. IC is deferred. AR and Grip need separate verification (§2.5).

### 1.2 Why this matters (unchanged)

Existing obs path blocks sim-to-real because real hardware cannot read Newton `body_q` for cable or clip. Even if current sim policy works, distribution shift on deployment is severe. Replacement must solve:

1. **Observability:** make target cable and clip pose measurable from robot sensors.
2. **Policy compatibility:** preserve policy architecture compatibility via fine-tuning, not re-design (AC-only for MVP-3, others later).

### 1.3 Non-goals (expanded)

This design does not authorize immediate implementation. It does **not** change:

- env reward definitions
- success conditions
- action space
- MSA skill routing semantics
- Newton VBD cable dynamics
- wrist camera manager internals
- training launch configuration
- **per-skill obs contract of AR / Grip / IC (v3 assumes current env code is authoritative until SSOT consolidation)**

First implementation is a **sidecar estimator** + offline evaluator, not an env-integrated policy dependency.

---

## 2. Design constraints

### 2.1 THREAD-specific constraints (unchanged from v2 + 3 additions)

| Constraint | Current value / implication |
| --- | --- |
| Physics backend | Newton VBD primary. PhysX is legacy (N-dependency bug at N>1). |
| Parallel worlds | W=32 batched (verified per `project_vbd_multiworld_verified.md`). |
| Cable representation | 40-body segmented rod, routing-plan target ± 1 window. |
| Wrist cameras | Left=body 6、Right=body 15 (FRANKA_NUM_JOINTS + EE_BODY_OFFSET)、128², FOV 45°. |
| Pixel scale | 0.86 mm/px at 133 mm working distance. |
| Task precision | T_DIST = 2 mm、T_GROOVE = 3 mm、EE_TO_FINGERTIP = 220 mm. |
| Existing camera overhead | W=32、C=2、128² RGB-D adds ~6% per step (A6000 cuda:0 render). |
| Policy contract | MSA 42D obs / 12D action for AC/AR/Grip; **IC is 45D (§1.1)**. |
| Clip geometry | 5 identical clips at known nominal placements; CAD assumed available. |
| **[v3] Newton VBD non-differentiability** | Cannot train surrogate via sim-differentiable gradients; supervised dataset generation from body_q required (CC3-3). |
| **[v3] wrist_camera_manager CPU scipy loop** | ~2 ms/step per `LL-VisualObs-CameraSystem.md:127`. Stage 0 must use Warp kernels, not inherit scipy path (CC3-4). |
| **[v3] GPU slot counts** | cuda:0 max 4 procs (A6000 48GB、sim pool)、cuda:2 max 4 procs (PRO 4000 24GB、train pool). Phase 5-1 4 DAPG skills saturate both (CC3-5). |

### 2.2 R6 observation-grounding constraint (unchanged statement, stricter v3 application)

From `Vision Pipeline.md` §R6 補足:

> センサ固有のデコード (画像→幾何量、音→周波数等) に学習を使用することは許容される。ただしデコード出力は物理モデルで制約し (Stage 3)、学習が物理量の定義を変更しないこと。

v3 R6 tests (**stricter** than v2):
1. Is learning restricted to sensor decoding only (Stage 1 segmentation)? → **Must be YES**
2. Do NN outputs quantitatively shape Stage 3 physical fit residual? → **Must be NO** (v3: binary point weights only)
3. Does NN confidence decide which physical source feeds policy? → **Must be NO for Stage 3 residual, OK for Stage 4 gating IF physical proxies are used**
4. Is the projection operator hard (idempotent) so DD-PINN warm-start cannot leak into final pose under degenerate inputs? → **Must be YES**
5. Does policy see unflagged regime changes (ACCEPT / PREDICT / FALLBACK)? → **Must be NO** — augmented obs with state bits required (v3 change from v2)

### 2.3 Primary acceptance criteria (tightened from v2)

| Gate | Target |
| --- | --- |
| Observation compatibility | AC-only MVP-3: obs[16:30] 14D + obs[30:42] 12D recomputed from est pose + 4D state one-hot + 1D confidence = 47D augmented policy obs. **Not** silent 42D substitution. |
| Position accuracy (AC target seg) | < 5 mm for MVP-2B、long-term target < 2-3 mm |
| Orientation accuracy (AC target seg) | < 0.05 rad for MVP-2B |
| Policy compatibility (AC) | ≥ 90% of GT baseline success over 100 eval episodes at MVP-3 |
| Performance | total (camera + estimator) overhead ≤ 12% of step wallclock, measured at MVP-2B |
| Debuggability | Each stage emits diagnostics; 11-code failure taxonomy + regime state machine fully logged |
| **[v3] R6 hard test** | zero-visible-points input must converge to prior-only fallback **without DD-PINN-shaped leakage** (integration test required) |
| **[v3] Cross-world isolation** | resetting world w cannot alter `prev_cable_state[w']` for w' ≠ w (unit test required) |
| **[v3] Quat convention** | `PoseEstimate13D.seg_quat_w` matches `newton_env.body_q[seg_idx, 3:7]` byte-for-byte over 100 random rotations (regression test) |

### 2.4 Observation contract break disclosure (v3 new, addresses CC5-8)

v3 explicitly declares: **the estimator integration is a semantic contract break**, not a drop-in replacement.

| Aspect | v2 claim | v3 corrected statement |
| --- | --- | --- |
| Shape | "preserves 42D contract" | Expands AC obs from 42D → 47D (+ 4D state + 1D confidence) |
| Semantics | Identity (GT pose) | Confidence-gated visual estimate with explicit regime state visible to policy |
| Policy weights | "subject to fine-tuning" | **Full fine-tuning required**; fresh start option if value_loss > 3× baseline at 20 iters |
| DR distribution | Identity under existing DR | Expanded DR (physics DR + estimator noise DR + occlusion DR) |

### 2.5 Per-skill SSOT consolidation (v3 new, blocker for MVP-4)

**Problem:** `RL-Routing-Design.md` §4 specifies a 42D "common" obs, but `newton_insert_clip_env.py` implements 45D groove-relative obs (verified 2026-04-25 via env read at lines 1165-1181). This is a SSOT divergence predating v3.

**Impact on v3:**
- AC / AR / Grip are **assumed** to follow RL-Routing-Design 42D (AR verified via grep on `newton_aerial_regrasp_env.py` — pending full verification TBD at MVP-3 time; similarly Grip).
- IC **differs**. Estimator for IC would have to produce groove-relative quantities (shape array + pos/ori error), not absolute world-frame pose.

**MVP-4 prerequisite (Rs decision, not CC autonomous):**

Before MVP-4 (IC/AR/Grip expansion), Rs must decide one of:
- **(A) Unify all 4 skills to RL-Routing-Design 42D** (IC env refactor required — large change)
- **(B) Maintain per-skill obs**, estimator has per-skill output heads
- **(C) Defer IC entirely** from pose estimation integration; keep IC on GT obs even in sim-to-real phase

No MVP-4 scoping is valid without Rs decision on (A/B/C). v3 does not preempt.

---

## 3. Target system overview

### 3.1 Dataflow (v3 revised)

```text
Wrist RGB-D + joint/body state + routing state + prev_est + CAD
        |
        v
Stage 0: kinematic prior + ROI + self-occlusion  (Warp kernel, per-world isolated)
        |
        v
Stage 1: multi-head segmentation  (cable / 5 clip / depth_valid / occlusion / confidence)
        |
        v
Stage 2: analytic depth back-projection + binary-weighted point cloud
        |
        v
Stage 3a: cable rod fitting (surrogate warm-start → HARD idempotent projection → robust refinement)
Stage 3b: clip CAD rigid pose fitting (5 instances; NO nominal fallback under DR)
        |
        v
Stage 4: physical-proxy confidence + regime state machine + smoothing (high-conf only)
        |
        v
obs_replacement_block + regime_state_bits + confidence_scalar + diagnostics
        |
        v
Policy obs (47D for AC MVP-3): obs[0:16] proprio + est_obs[16:30] + recomputed_error[30:42] + state[42:46] + conf[46]
```

### 3.2 Output contract (v3 revised with regime state + confidence)

```python
from dataclasses import dataclass
import torch

@dataclass
class PoseEstimate14D:
    """AC/AR/Grip contract, not IC.

    All tensors have shape prefix [W, ...] where W = parallel world count.
    Quaternions: xyzw convention, canonicalized w >= 0 byte-for-byte
    matched to Newton body_q (verified by regression test).
    """
    seg_pos_w: torch.Tensor    # [W, 3], float32, m (SI)
    seg_quat_w: torch.Tensor   # [W, 4], float32, xyzw w>=0
    clip_pos_w: torch.Tensor   # [W, 3], float32, m
    clip_quat_w: torch.Tensor  # [W, 4], float32, xyzw w>=0

    def as_obs_block(self) -> torch.Tensor:
        """Returns [W, 14] matching obs[16:30] for AC/AR/Grip."""
        return torch.cat(
            [self.seg_pos_w, self.seg_quat_w, self.clip_pos_w, self.clip_quat_w],
            dim=-1,
        )


@dataclass
class RegimeState:
    """Stage 4 output, shape [W, ...] per world."""
    state: torch.Tensor   # [W], int8, 0=ACCEPT, 1=PREDICT, 2=FALLBACK, 3=FAIL_CLOSED
    confidence: torch.Tensor  # [W], float32, [0,1] heuristic gate (MVP-0..2)
    fresh_visual: torch.Tensor  # [W], bool, True if current frame vision passed primary gate

    def as_policy_obs_extension(self) -> torch.Tensor:
        """Returns [W, 5]: 4D one-hot state + 1D confidence, appended to 42D → 47D."""
        onehot = torch.nn.functional.one_hot(self.state.long(), num_classes=4).float()
        return torch.cat([onehot, self.confidence.unsqueeze(-1)], dim=-1)


@dataclass
class PoseEstimatorDiagnostics:
    """Not in policy obs; logged only."""
    cable_mask_area: torch.Tensor        # [W], float32, pixel count normalized by 128^2 → [0,1]
    clip_mask_area: torch.Tensor         # [W, 5], same normalization
    cable_point_count: torch.Tensor      # [W], int32
    clip_point_count: torch.Tensor       # [W, 5], int32
    cable_fit_residual_mm: torch.Tensor  # [W], float32, mm (SI)
    clip_fit_residual_mm: torch.Tensor   # [W, 5], float32, mm
    seg_confidence: torch.Tensor         # [W], float32, [0,1] physical-proxy (NOT NN output)
    clip_confidence: torch.Tensor        # [W, 5], float32, [0,1] physical-proxy
    used_prediction: torch.Tensor        # [W], bool — True if regime=PREDICT
    used_nominal_clip: torch.Tensor      # [W, 5], bool — True if regime=FALLBACK for that clip
    failure_code: torch.Tensor           # [W], int8, enum (§9.4)
    projection_iterations: torch.Tensor  # [W], int32, Stage 3a projection LM iters
    projection_converged: torch.Tensor   # [W], bool, True if projection reached tolerance
```

**SI units** (AGENTS.md docstring rule + CC4-9):
- position: m
- orientation: rad (axis-angle) / unitless normalized (quat)
- residual: mm
- confidence: dimensionless [0, 1]
- mask area: dimensionless [0, 1] (normalized pixel count)
- point count: int (integer count)

### 3.3 Responsibility boundary (v3 unchanged from v2)

| Module | Responsibility | Explicitly not responsible for |
| --- | --- | --- |
| `WristCameraManager` | RGB-D tensors + camera transforms | Estimator inference, policy obs mutation |
| `PoseEstimatorV1` | Convert visual/proprio inputs to PoseEstimate14D + RegimeState + Diagnostics | Reward calculation, skill routing, training |
| `ObsAssembler` (env wrapper) | Replace obs[16:30] + recompute obs[30:42] from est + append state+conf | Camera rendering, segmentation training |
| `EvalPoseEstimator` | Compare est vs sim GT offline | Policy optimization |
| `TrainSegmenter` | Stage 1 training on sim synthetic labels | Env integration |

---

## 4. Architecture choice

### 4.1 Option comparison (v2 table retained for reference, v3 adds an R6 hard-test row)

| Axis | A: Pure geometry | B: Pure NN | **C: Hybrid (v3 C-2R)** | D: Diff render |
| --- | --- | --- | --- | --- |
| R6 alignment | Strong | Weak | **Strong (hard projection)** | Strong |
| R6 hard test (zero-vis → prior-only) | N/A (no NN) | Fails | **Passes with hard projection** | Passes |
| 2 mm feasibility | Medium-low | Uncertain | **Medium-high** | High |
| Occlusion handling | Weak | Medium | Medium-high | Medium |
| Sim-to-real risk | Low-medium | High | Low-medium | Low-medium |
| W=32 feasibility | Medium | High | **Medium-high** | Low-medium |
| Debuggability | High | Low | **High** | Medium |
| Implementation risk | Medium | Medium | **Medium** | High |
| Recommended role | Baseline / ablation | Rejected for final pose | **Primary design** | Long-term refinement |

### 4.2 Why Option C-2R remains the right default (v2 rationale + v3 hardening)

Option C isolates learning to the least-dangerous pipeline segment: segmentation. Physical pose is produced by geometry, depth, CAD constraints, and cable continuity. v3 makes the R6 boundary enforceable via:

- **Hard idempotent projection** (§5.4): DD-PINN warm-start cannot leak past projection into final pose
- **Binary point weights** (§5.3): NN segmentation probability gates inclusion (threshold > 0.5), never rescales Stage 3 residual
- **Physical-proxy confidence** (§5.6): Stage 4 gate uses point_count + fit_residual + depth_valid_fraction, **not** NN mask_confidence
- **Augmented obs** (§6.1): regime state + confidence are visible to policy, not hidden behind a stable 13D/14D float vector

### 4.3 Recommended variant: C-2R (v3 refined)

| Variant | v2 status | v3 status |
| --- | --- | --- |
| C-1 SAM2 + full Cosserat | Keep as later variant | **Kept as later ablation** |
| C-2 light U-Net + DD-PINN | Underspecified | **Superseded by C-2R** |
| **C-2R** routing-conditioned + hard projection + augmented obs | **Recommended** | **Recommended (hardened for R6)** |
| C-3 Isaac Sim oracle seg + full rod | Sim-only baseline | **Kept as sim-only baseline ablation** |

### 4.4 C-2R v3 hardening summary (new vs v2)

| v2 weakness | v3 fix |
| --- | --- |
| Projection operator undefined | §5.4 specifies projection P as hard idempotent on 40-seg Cosserat manifold (P(P(x)) = P(x)) + convergence test |
| NN output influences Stage 3 residual via soft weights | Binary weights only (§5.3 threshold > 0.5); soft weights logged to diagnostics not used in fit |
| NN mask_confidence decides obs source in Stage 4 | Physical proxies (point_count, fit_residual, depth_valid_fraction) gate Stage 4 (§5.6) |
| Stage 4 regime hidden from policy | Policy obs augmented with one-hot state + confidence scalar (§6.1) |
| FALLBACK_NOMINAL_CLIP under DR = lie | **Forbidden when DR is active on clip pose** (§5.5 + §10 risk register) |
| Segment-index monotonicity in image space | Arc-length monotonicity in Cosserat rod space (§5.4) |
| Smoothing IIR at low confidence | Alpha = 1.0 (no smoothing) required unless confidence exceeds high-conf threshold; high-conf smoothing OK (§5.6) |
| "Preserves 42D contract" claim | Replaced with "semantic contract break, 42D → 47D for AC MVP-3" disclosure (§2.4) |

---

## 5. C-2R stage specifications (v3 revised)

### 5.1 Stage 0: kinematic prior and ROI proposal (Warp-kernel mandate)

#### Objective (unchanged)

Reduce the visual search problem before segmentation using information already available to the robot.

#### Inputs (v3 adds per-world isolation contract)

| Input | Shape | Notes |
| --- | --- | --- |
| `joint_state` | `[W, J]` | Arm joint positions/velocities |
| `body_q_snapshot` | `[W, B_total, 7]` | **Same** `state.body_q` passed to `SensorTiledCamera.update` (frame alignment contract — unit test required) |
| `prev_cable_state` | `[W, 40, 7]` | Previous estimate; **per-world indexed writes only** (RESET-EE isolation, CC4-4) |
| `routing_state` | `[W, ...]` | current target seg / clip index |
| `nominal_clip_poses` | `[5, 7]` | Static prior from task_config |

#### Per-world isolation contract (v3 new, CC4-4)

```python
# MANDATORY for all W-indexed tensors:
# - tensor[w, :, ...] is owned by world w alone
# - World w's reset clears tensor[w] only; never tensor[w'] for w' != w
# - Stage 0/1/2/3 must not use shared scratch buffers that write cross-world
# - Unit test: reset world 3 → assert tensor[0].pre == tensor[0].post (bit-equal)
```

#### Outputs (unchanged from v2)

| Output | Shape | Purpose |
| --- | --- | --- |
| `roi_l`, `roi_r` | `[W, K, 4]` | Camera-space boxes for cable+clip target regions |
| `self_occlusion_mask_l/r` | `[W, 1, 128, 128]` | Projected gripper/body pixels |
| `target_segment_prior` | `[W, 40]` | ±1 window centered on routing target |
| `clip_prior` | `[W, 5]` | target clip softened one-hot |

#### ROI construction + self-occlusion mask (v3 Warp-kernel mandate)

Per CC3-4, Stage 0 must use Warp kernel batched over W × (per-world projection points). **scipy CPU loop is forbidden**. Prerequisite:

1. `wrist_camera_manager.py:115-151` scipy-loop refactor must complete (or be scheduled concurrent with MVP-0A) — noted in §12 implementation checklist as prerequisite
2. Stage 0 Warp kernel benchmarks: target ≤ 2 ms / step at W=32 for 5 clip + 40 seg + gripper-mesh projection (measured-TBD at MVP-0A)

#### Frame alignment contract (v3 new, CC3-6)

Stage 0 must read `body_q` from the **same** snapshot that was passed to `SensorTiledCamera.update(state_0, ...)` for the current render. Explicit API:

```python
def run_stage_0(
    body_q_for_render: torch.Tensor,  # SAME snapshot as render; caller responsibility
    routing_state: ...,
    ...
) -> Stage0Output:
    ...
```

Unit test: `id(body_q_for_render) == id(body_q_passed_to_camera_update)` or per-step hash equality.

### 5.2 Stage 1: segmentation with multi-head output (v3 expanded)

#### Objective (unchanged)

Convert wrist RGB into instance-aware masks for cable + 5 clips + auxiliary signals.

#### Inputs (unchanged)

| Input | Shape |
| --- | --- |
| `rgb_l`, `rgb_r` | `[B, 3, 128, 128]` with B = W_world (use B, not W, to avoid symbol overload — CC2-6) |
| `depth_l`, `depth_r` | `[B, 1, 128, 128]` |
| `camera_pose_l/r` | `[B, 7]` |
| Stage 0 outputs | as above |

#### Outputs (v3 fixes CC2-6 symbol, CC2-3 confidence breakdown)

| Output | Shape | Notes |
| --- | --- | --- |
| `cable_prob` | `[B, 2, 128, 128]` | one binary map per camera (B=W_world) |
| `clip_prob` | `[B, 2, 5, 128, 128]` | instance masks, 5 clips |
| `depth_valid_prob` | `[B, 2, 1, 128, 128]` | auxiliary |
| `occlusion_prob` | `[B, 2, 1, 128, 128]` | auxiliary |
| `seg_confidence_raw` | `[B]` scalar per world | NN-derived, **only used in diagnostics**, not in Stage 4 gate |
| `clip_confidence_raw` | `[B, 5]` | NN-derived per-instance, **only in diagnostics** |

#### Model recommendation + memory budget (v3 new, CC3-1/CC3-2)

**Measured-benchmark gate** (Rs OQ-1 approval prerequisite):

Before OQ-1 is approved, a measured benchmark must be produced by replaying cached wrist RGB-D from an AC episode through the candidate Stage 1 model. Gates:

| Metric | Target (measured, p50 / p99) |
| --- | --- |
| Stage 1 forward latency at B=32, C=2, 128² | p50 ≤ 20 ms、p99 ≤ 35 ms |
| Memory: Stage 1 forward max VRAM (fp16) at B=32 | ≤ 3 GiB (headroom ≥ 2 GiB on cuda:2 24 GiB alongside MSA training) |
| Memory: Stage 1 training max VRAM (fp32 grad) at B=32 | ≤ 12 GiB (solo on cuda:2; training offline, not concurrent with MSA training) |

Candidate models (revised from v2 list):

| Candidate | Forward latency estimate (un-measured) | Use |
| --- | --- | --- |
| Light U-Net (< 2M params, fp16 inference) | ~15-25 ms @ B=64 (9 output maps on 128²) | **MVP-0A default candidate** |
| Fast-SCNN-style encoder-decoder | ~10-15 ms | Fallback if U-Net fails latency gate |
| BiSeNet-style | ~12-18 ms | Alternative |
| SAM2 fine-tune | >100 ms, >10 GiB | Ablation-only, never MVP dependency |
| Isaac Sim semantic seg oracle | n/a | Sim-only oracle for ablations |

**Memory budget** (v3 new, §8.1 refinement):

| Item | Budget at B=32, C=2, 128², fp16 |
| --- | --- |
| Stage 1 model weights | ~10-50 MiB (2M params × 2 bytes) |
| Stage 1 forward activations | ~500 MiB - 1.5 GiB (depends on U-Net depth) |
| 9 output maps | ~8 MiB |
| Stage 2 point clouds (padded, N_cable_max=1024, N_clip_max=256 × 5) | ~60 MiB |
| Stage 3a state tensors (40 seg × 7D × B=32) | ~35 KiB |
| Stage 3a robust loss intermediates | ~500 MiB (worst-case with point-wise residual gradients) |
| **Estimator total VRAM (inference)** | **~2-3 GiB target** |
| MSA training (actor + critic + optimizer + replay) | ~8-10 GiB baseline |
| Headroom required | **≥ 2 GiB** |

**Rule:** estimator + MSA training combined must fit in cuda:2 24 GiB with ≥ 2 GiB headroom.

#### Loss design (v3 fixes Σw constraint, CC2-3 partial)

```text
L_stage1 =
  L_dice(cable) + L_focal(cable)
+ L_dice(clip_instances) + L_focal(clip_instances)
+ lambda_depth * L_bce(depth_valid)
+ lambda_occ   * L_bce(occlusion)

# lambda_depth, lambda_occ in [0.1, 0.5] range
# Main losses (dice + focal for cable and clip) at weight 1.0 unless profiling shows imbalance
```

#### Data randomization (v3 slight addition, unchanged essence)

Randomize: cable color/texture、clip color/material、table/background、lighting、camera exposure/noise、slight extrinsic perturbation、finger/gripper visibility、cable shape/routing phase、**clip DR pose perturbation (to feed §5.5 FALLBACK_NOMINAL_CLIP forbidden-under-DR test)**.

### 5.3 Stage 2: point cloud with BINARY weights (v3 R6 hardening, CC5-4)

#### Objective

Back-project valid masked depth into world-frame point clouds, with **binary** (not NN-soft) point weights.

#### Required operations (v3 CC5-4 change in bold)

1. Apply cable and clip masks to depth
2. Reject invalid / saturated depth
3. Back-project via camera intrinsics (Warp kernel, CC3-4)
4. Transform camera-frame → world-frame (using Stage 0's body_q snapshot)
5. Merge left/right camera clouds (concat + voxel dedup)
6. Subsample to bounded point budget (N_cable_max=1024, N_clip_max=256 per clip)
7. **Attach binary weights (threshold > 0.5 on segmentation prob); soft weights logged to diagnostics only, not used in Stage 3 residual**

#### Robust filtering (unchanged)

- Depth range clipping around projected ROI
- Statistical outlier removal in world frame
- Robot self-mask removal
- **Confidence-weighted sampling** for inclusion only (NOT for residual scaling)
- Voxelization to prevent background dominance

#### Failure gate (v3 stricter)

- If cable point count < N_cable_min (e.g., 50) → `SEG_EMPTY_CABLE` + regime=PREDICT if fresh, else FAIL_CLOSED
- If any target clip point count < N_clip_min (e.g., 20) → `SEG_EMPTY_CLIP` + FAIL_CLOSED (NO nominal fallback under DR, §5.5)

### 5.4 Stage 3a: cable rod fitting with HARD idempotent projection (v3 R6 hardening, CC5-1)

#### Objective

Estimate 40-seg rod state, then select routing target seg.

#### Fit variables

```text
q_cable ∈ R^{40 × 7} = [seg_0_pos, seg_0_quat, ..., seg_39_pos, seg_39_quat]
```

#### Loss terms (v3 fixes CC5-7 monotonicity)

| Term | Purpose | Lambda |
| --- | --- | --- |
| Point-to-rod distance (robust ρ) | Align visible rod surface to point cloud | 1.0 (baseline) |
| Segment length consistency | Preserve 40-seg rod geometry (task_config L_seg) | λ_len |
| C0/C1 continuity | Segment-to-segment continuity | λ_cont |
| Bending regularization | Stabilize occluded / straight portions | λ_bend |
| Temporal prior | Small delta from prev frame unless high-confidence evidence | λ_temp |
| Routing-local weighting | Higher weight near target segment ± 1 window | λ_roi (training-time **must be 0 or in diagnostics only** for estimator-induced distribution shift eval — CC5-6) |
| **Arc-length monotonicity** (v3 replaces image-space monotonicity) | Segment i centerline at arc-length i·L_seg from seg_0 along rod, **not in image coordinates** (CC5-7) | λ_arc |

```text
L_cable = ρ(point_to_rod, binary_weights)
        + λ_len · segment_length_error
        + λ_cont · C0_C1_error
        + λ_bend · bend_energy
        + λ_temp · temporal_delta_error
        + λ_arc  · arc_length_monotonicity_error
        + λ_roi  · target_window_error  # training-off-by-default
```

Robust ρ: Huber / Tukey / trimmed LS (per §9.3 ablation).

#### Recommended solver structure (v3 with hard projection)

```text
point_cloud (binary weighted) + priors
        |
        v
Surrogate warm-start  (DD-PINN if trained, OR analytic tangent-from-PCA per segment)
        |
        v
Hard idempotent projection  P  onto 40-seg Cosserat manifold  →  P(P(x)) = P(x)
        |
        v
Robust local refinement  (Levenberg-Marquardt, max 10 iters, Jacobian batched in Warp)
        |
        v
Final 40-seg state + per-seg residual + global residual + fit confidence (physical)
```

#### Hard idempotent projection operator P (v3 CC5-1 mandate)

Defined as:

```text
P(q) = argmin_{q' ∈ M} ||q - q'||^2_M

M = { q = [seg_i (pos, quat) | i = 0..39] :
      (a) ||q[i+1].pos - q[i].pos|| - L_seg  =  0    (hard equality)
      (b) ||q[i].quat|| = 1  AND  q[i].quat.w >= 0    (hard)
      (c) dot(q[i].quat_axis, q[i+1].quat_axis) > cos(theta_max)  (hard, continuity)
      (d) q[i].pos ∈ workspace_AABB   (hard)
      (e) || q[i].pos - q_prev[i].pos || <= d_max(i, confidence)   (hard, per-seg displacement bound)
}
```

Implementation: one-step Gauss-Newton on lifted constraints + dual-ascent + single projection pass. Convergence test: max ||residual|| < 1e-6 in world-frame meters or quat angular.

Idempotency test (**unit test required**): input q' = P(q0) for arbitrary q0 → assert P(q') == q' within 1e-8 tolerance.

**R6 hard test** (integration test required, §9): feed zero-visible-points scenario → assert output = `P(prior_only)` and is NOT influenced by DD-PINN warm-start content (bit-comparable to prior-projected vs surrogate-projected).

#### Degeneracy handling (unchanged essence, slight refinement)

Straight sections / partial visibility → prioritize position over quat, derive tangent from neighbor seg, smooth quat temporally, expose orientation-confidence diagnostic per seg.

#### Segment identity handling (v3 arc-length based, CC5-7)

v2 used "segment-index monotonicity" in image space — v3 replaces with **arc-length monotonicity** (Cosserat physical law):

```text
arc_length(seg_i, rod_centerline) = Σ_{j=0..i-1} L_seg(j) = i · L_seg  (equi-spaced rod)

Constraint (hard): assignment of observed points to segments satisfies
  arc_length(point_p, assigned_seg) monotone non-decreasing along rod centerline
```

This permits physical kinks (self-occlusion U-bend, tight routing) while preventing nonphysical segment swaps.

#### DD-PINN surrogate applicability note (v3 new, CC3-3)

**Status:** The 2025 DD-PINN paper (continuum Cosserat) requires adaptation for THREAD's 40-seg discrete rigid VBD rod. Adaptation cost:

| Item | Estimated cost |
| --- | --- |
| Training dataset generation | 100k sim frames from batched AC + IC + AR episodes (W=32 × ~500 steps × 100 episodes); ~20 min at current 2.1 Hz step rate; storage ~5 GB |
| Supervised training on cuda:2 | 1-2 days (4-head regression, MLP with PINN constraints) |
| Domain transfer evaluation | compare surrogate proposal convergence-basin-fraction at various occlusion levels |

**Alternative (fallback 1):** Analytic tangent-from-PCA per segment (no NN):
- Project point cloud onto principal axis of local neighborhood → tangent direction
- seg_pos[i] = cluster centroid along rod centerline at arc-length i·L_seg
- seg_quat[i] = tangent-aligned frame

This fallback is R6-stronger than DD-PINN and avoids dataset/training cost. **Recommended as MVP-2A default** pending DD-PINN cost-benefit analysis.

**Alternative (fallback 2):** No surrogate, projection directly initialized from `prev_cable_state`. Works when prev state is fresh (confidence > threshold).

### 5.5 Stage 3b: clip CAD fitting, NO FALLBACK_NOMINAL_CLIP under DR (v3 CC5-3)

#### Objective

Estimate 5 rigid clip poses from per-instance clip point clouds and CAD.

#### Recommended fit (unchanged)

1. Initialize each clip at nominal `task_config.py` pose
2. Associate observed clip points with CAD surface (nearest-face mapping)
3. Solve rigid transform via closed-form SVD (or ICP for refinement)
4. Constrain by workspace
5. Select target clip via routing state

#### Fallback (v3 stricter than v2, CC5-3)

| Condition | Fallback permitted | Diagnostics flag |
| --- | --- | --- |
| DR on clip pose **off** (training-time fixed clips) AND visual confidence low | Nominal pose OK with explicit `used_nominal_clip[w, c]=True` | YES |
| DR on clip pose **on** (DR active) | **FORBIDDEN** — FAIL_CLOSED for that clip | YES |

Rationale: under DR the nominal `task_config` pose is guaranteed wrong (that is DR's purpose). Using nominal during DR-on training = feeding a known lie to policy = R6 violation (§2.2 test 1).

### 5.6 Stage 4: probabilistic temporal consistency and fallback gate (v3 major revision)

#### Objective

Reduce jitter, prevent single-frame failures, and **never silently substitute obs source without notifying policy** (v3 augmented obs, CC5-2).

#### State machine (unchanged)

| State | Meaning | Policy obs source for obs[16:30] |
| --- | --- | --- |
| `ACCEPT_VISUAL` | Current visual passes gates | current Stage 3 estimate |
| `PREDICT_TEMPORAL` | Current visual weak, previous fresh, dynamics smooth | predicted previous estimate |
| `FALLBACK_NOMINAL_CLIP` | Clip visual failed, DR **off**, nominal trusted | nominal clip pose (seg part is PREDICT or FAIL depending on cable state) |
| `FAIL_CLOSED` | Unsafe / stale / FALLBACK under DR | **last accepted pose** (or zero-filled with flag — to be decided Rs at MVP-2C) |

#### Policy visibility of regime (v3 new, CC5-2)

Regime state is **not hidden**. Policy obs is augmented:

- AC MVP-3 policy obs: `[42D MSA obs, one_hot_state (4D), confidence (1D)] = 47D`
- 4D one-hot: ACCEPT=[1,0,0,0], PREDICT=[0,1,0,0], FALLBACK=[0,0,1,0], FAIL_CLOSED=[0,0,0,1]
- Policy learns to be cautious during non-ACCEPT regimes

This is a **contract break** from 42D → 47D (§2.4 disclosed). Fresh fine-tuning with state bits is required.

#### FAIL_CLOSED semantics (v3 explicit, CC4-2)

```python
def on_fail_closed(world_idx):
    # Termination mapping (prohibited.md timeouts汚染 prevention)
    dones[world_idx] = True
    extras["time_outs"][world_idx] = False   # MANDATORY: False
    # obs[16:30] content: last accepted or zero (Rs decision at MVP-2C; default: zero + regime bit)
    # Policy will see state=FAIL_CLOSED via augmented obs and can learn to act cautiously
```

**Mandatory integration test:**
```python
def test_fail_closed_timeouts():
    trigger_fail_closed(world=5)
    assert dones[5] == True
    assert extras["time_outs"][5] == 0   # CRITICAL: must not be True
```

#### Confidence score (v3 physical proxies, CC5-9)

```text
conf =
  w_pts   * point_count_score
+ w_fit   * exp(-fit_residual / tau_fit)
+ w_depth * depth_valid_fraction
+ w_temp  * temporal_consistency
+ w_occ   * (1 - occlusion_fraction)

where Σ w_i = 1 (constraint)
Default weights: (w_pts, w_fit, w_depth, w_temp, w_occ) = (0.25, 0.30, 0.15, 0.20, 0.10)

point_count_score = min(1, N_pts / N_ref)     # N_ref = 200 for cable, 50 for clip
fit_residual      = Stage 3 per-world residual in mm; tau_fit = 5 mm (cable), 3 mm (clip)
depth_valid_fraction = fraction of masked pixels with valid depth, [0,1]
temporal_consistency = exp(-||p_t - p_{t-1}||_mm / tau_temp); tau_temp = 10 mm
occlusion_fraction = fraction of ROI pixels flagged self-occluded, [0,1]
```

**Note:** NN `mask_confidence` is **NOT** in the gating formula. It is logged in diagnostics as `seg_confidence_raw` for calibration analysis but does not route obs source.

#### Update policy (unchanged from v2)

```python
if conf >= T_high:
    regime = ACCEPT
elif prev_state_fresh and conf >= T_predict:
    regime = PREDICT
elif clip_fit_failed and not dr_active:
    regime = FALLBACK
else:
    regime = FAIL_CLOSED
```

Thresholds `T_high, T_predict` are MVP-2C calibrated.

#### Smoothing (v3 stricter, CC5-5)

```text
if regime == ACCEPT_VISUAL and conf >= T_smooth_high:
    p_out = α * p_current + (1 - α) * p_previous      # α ∈ [0.7, 0.9] (slight smoothing)
    q_out = slerp(q_previous, q_current, α)
elif regime == ACCEPT_VISUAL and conf in [T_smooth_low, T_smooth_high):
    p_out = p_current     # α = 1.0, no smoothing
    q_out = q_current
elif regime == PREDICT_TEMPORAL:
    # Cosserat-consistent prediction (v3 replaces v2's linear IIR)
    p_out, q_out = cosserat_predict_one_step(prev_state, dt_since_last_accept)
else:
    p_out, q_out = per-regime fallback
```

**Key change:** low-confidence linear IIR blending is **removed**. Predict uses Cosserat dynamics propagation from `prev_state` (analytic, not NN). This removes the "implicit NN dynamics model" CC5-5 concern.

#### Suggested update cadence (unchanged)

| Phase | Cadence |
| --- | --- |
| Approach / move | 5-10 Hz |
| Close manipulation | 20 Hz if possible, else every env step with camera |
| Static clip | Lower (once per N steps) |

Measured at MVP-2B.

---

## 6. Observation integration (v3 major revision)

### 6.1 Per-skill replacement mapping (v3 new, CC4-1)

Because per-skill obs contract differs (§1.1, §2.5):

| Skill | Current obs | Replacement scope for MVP-3 |
| --- | --- | --- |
| **AC** | 42D | obs[16:30] est + obs[30:42] recompute + append 5D (state + conf) → **47D** |
| AR | 42D (assumed; env verify TBD) | Pending §2.5 SSOT consolidation |
| Grip | 42D (assumed; env verify TBD) | Pending §2.5 SSOT consolidation |
| **IC** | 45D groove-relative | Architecturally different — estimator head for groove-relative pos/ori/shape; deferred MVP-4 post-SSOT |

**v3 default: AC-only MVP-3 integration.**

### 6.2 Error observation recomputation (v3 exhaustive, CC2-4)

For AC / AR / Grip (once verified), `obs[30:42]` 12D is recomputed from est pose. Indices use Python slice (off-by-one from v2 inclusive notation):

```python
# AC env obs contract
# obs[16:19] = est_seg_pos_w   (3D)
# obs[19:23] = est_seg_quat_w  (4D, xyzw w>=0)
# obs[23:26] = est_clip_pos_w  (3D)
# obs[26:30] = est_clip_quat_w (4D)

# Error block obs[30:42] (12D) derived per current env helpers:
hand_R_quat = proprio_based  # known
hand_R_clamp_pos = ee_pos + rotate(ee_quat, [0, 0, -EE_TO_FINGERTIP])  # known via proprio
# ... similarly hand_L

obs[30:33] = axis_angle(quat_diff(hand_R_quat, est_seg_quat_w))
obs[33:36] = hand_R_clamp_pos - est_seg_pos_w
obs[36:39] = axis_angle(quat_diff(hand_L_quat, est_seg_quat_w))
obs[39:42] = hand_L_clamp_pos - est_seg_pos_w

# FAIL_CLOSED regime: est_seg_{pos,quat}_w = last_accepted (or zeroed)
#   The recomputed error block propagates est through; policy sees regime=FAIL via aug-obs
```

**Convention notes:**
- `axis_angle(quat_diff(...))`: quat_diff is shortest-geodesic; axis_angle uses canonical Rodrigues. Match env helpers bytewise.
- `quat_diff` double-cover: enforce result `w >= 0`.
- `hand_R_clamp_pos` = body 6 pos + rotated finger offset (EE_TO_FINGERTIP). Same for hand_L body 15.

### 6.3 Noise injection path (v3 unchanged statement, stronger wording)

Pre-estimator training uses simulated noise:

```python
est_seg_pos_w  = gt_seg_pos_w  + N(0, σ_pos · I_3)
est_seg_quat_w = perturb_quat(gt_seg_quat_w, σ_ori)  # axis-angle perturb, quat exp
```

Placeholder initial values (must NOT be frozen as design truth):

| Parameter | Initial | Final source |
| --- | --- | --- |
| σ_pos | 3 mm | measured estimator residual at MVP-2B |
| σ_ori | 0.03 rad | measured estimator residual at MVP-2B |

v3 adds explicit measurement-driven requirement: MVP-3 AC integration requires DR noise std calibrated against MVP-2B measured residual; use of placeholder values in MVP-3 is failure to close the noise loop.

### 6.4 Augmented obs for AC MVP-3 (v3 new, CC5-2)

AC policy obs at MVP-3:

```
[0:42]  MSA 42D obs (existing)
[42:46] regime one-hot: [ACCEPT, PREDICT, FALLBACK, FAIL_CLOSED]
[46]    confidence scalar ∈ [0, 1]
```

Total 47D.

Policy architecture: modify AC policy head input dim 42 → 47. Fine-tune from AC GT checkpoint with state bits init to [1, 0, 0, 0] (ACCEPT) and confidence 1.0 (so initial behavior mimics GT obs under high confidence).

---

## 7. MVP roadmap (v3 with AC-only restriction + debate fixes)

### 7.1 Phased implementation (v3 revised)

| Phase | Scope | Exit criteria (measurable) |
| --- | --- | --- |
| MVP-0A | Stage 0 ROI + Stage 1 segmentation; wrist_L only; AC environment; offline replay (no cuda:0 sim slot) | cable mIoU > 0.8、5-clip mIoU > 0.75、ROI recall > 0.95、depth-valid AUROC > 0.85、occlusion AUROC > 0.80 |
| MVP-0B | Add wrist_R + self-occlusion masking | target visibility improves > 10pp vs MVP-0A、FP on gripper/body < 5% pixel ratio |
| MVP-1 | Stage 2 + binary weights + robust filtering; two cameras | cable > 200 valid points in ≥ 90% of frames、each visible clip > 50 points |
| MVP-2A | Stage 3a surrogate warm-start ONLY; no integration | surrogate proposal within projection basin ≥ 90% of frames (basin = 10 LM iters reduce residual ≥ 90%) |
| MVP-2B | Stage 3 with hard projection + robust refinement | cable target seg pos error < 5 mm、ori error < 0.05 rad、projection P(P(x))=P(x) bit-idempotent test PASSES、zero-vis R6 hard test PASSES |
| MVP-2C | Stage 4 confidence/fallback state machine + Cosserat smoothing | ACCEPT/PREDICT/FALLBACK labels rank-correlate with measured residual (> 0.7)、FAIL_CLOSED timeouts test PASSES、bias < 0.5 mm / 0.005 rad PREDICT_TEMPORAL |
| MVP-3 (AC-only) | Replace AC obs[16:30] + recompute obs[30:42] + augmented obs 47D + fine-tune AC policy | AC success ≥ 90% of GT baseline over 100 eval episodes; per-world isolation test PASSES; quat convention test PASSES; value_loss rollback rule: > 3× baseline at 20 iters → fresh init |
| MVP-4 | **DEFERRED** pending Rs decision on §2.5 (A/B/C) for IC/AR/Grip contracts | N/A |

### 7.2 MVP-0A first ticket (v3 with offline replay scope)

```text
Implement sidecar Stage 0 + Stage 1 segmentation evaluator on wrist RGB (offline replay).

Scope:
- Create thread_isaac_lab/estimators/ package (new directory, no conflict with existing scripts).
- Implement roi_prior.py, self_occlusion.py (Warp kernels per CC3-4 mandate).
- Implement segmenter.py with light U-Net + 9-head output.
- Add train_segmenter.py for supervised training on sim labels.
- Add eval_pose_estimator_mvp0a.py as offline evaluator replaying cached wrist RGB-D.
- Generate sim-label dataset (AC scenarios, W=32, ~100k frames) via existing sim episodes.
- Report mIoU, ROI recall, AUROC per gate.

Out of scope:
- env observation replacement
- policy finetune
- Cosserat fitting
- clip ICP
- real robot data
- MSA training contention on cuda:2 (training happens solo when slot available)
```

### 7.3 MVP-2 split rationale (unchanged from v2)

Split into 2A / 2B / 2C because cable pose estimation fails in different ways:

| Subphase | Proves | Why separate |
| --- | --- | --- |
| MVP-2A | Surrogate can produce plausible rod state fast | If fails, surrogate is not useful as warm start |
| MVP-2B | Constrained projection makes state physically valid & accurate (R6-critical) | Must be tested independently from surrogate |
| MVP-2C | Confidence/fallback decisions match actual residuals | Good mean residual insufficient if failures are silent |

### 7.4 Suggested files (v3 verified non-duplicate per feedback_check_existing_eval_grep.md)

**Existing eval scripts** (verified 2026-04-25 grep): `eval_aerial_regrasp.py`, `eval_approach_cable.py`, `eval_deterministic.py`, `eval_reward_components.py`, `eval_skill.py` — all policy evaluators, **not** pose-estimator evaluators. No duplication.

**Existing directories:** `thread_isaac_lab/scripts/` (populated), `thread_isaac_lab/envs/` (populated), **`thread_isaac_lab/estimators/` does not exist** — new directory OK.

| File | Purpose | Conflict check |
| --- | --- | --- |
| `thread_isaac_lab/estimators/__init__.py` | package marker | new, no conflict |
| `thread_isaac_lab/estimators/pose_estimator_v1.py` | top-level interface | new |
| `thread_isaac_lab/estimators/roi_prior.py` | Stage 0 ROI, Warp kernel | new |
| `thread_isaac_lab/estimators/self_occlusion.py` | Stage 0 self-mask, Warp kernel | new |
| `thread_isaac_lab/estimators/segmenter.py` | Stage 1 model + training wrapper | new |
| `thread_isaac_lab/estimators/depth_projector.py` | Stage 2 back-projection, Warp kernel | new |
| `thread_isaac_lab/estimators/cable_fit.py` | Stage 3a rod fitting | new |
| `thread_isaac_lab/estimators/rod_surrogate.py` | DD-PINN or PCA tangent warm-start | new |
| `thread_isaac_lab/estimators/projection.py` | hard idempotent P operator | new |
| `thread_isaac_lab/estimators/clip_fit.py` | Stage 3b CAD fitting | new |
| `thread_isaac_lab/estimators/temporal_gate.py` | Stage 4 state machine | new |
| `thread_isaac_lab/scripts/train_segmenter.py` | Stage 1 training | new |
| `thread_isaac_lab/scripts/eval_pose_estimator_mvp0a.py` | MVP-0A evaluator (not dup of existing) | new |
| `thread_isaac_lab/scripts/eval_pose_estimator_mvp0b.py` | MVP-0B | new |
| `thread_isaac_lab/scripts/eval_pose_estimator_mvp2.py` | residual evaluator | new |

Provisional until repository conventions are checked at impl time.

---

## 8. Performance budget (v3 measured-gate + memory + per-MVP cumulative)

### 8.1 Per-MVP cumulative overhead (v3 new, CC2-5)

| MVP | Stages active | Estimator overhead target (ms/step at W=32, C=2, 128²) | Cumulative total step time | % of baseline |
| --- | --- | --- | --- | --- |
| baseline (no estimator) | render only | 28.6 ms render | ~478 ms | 6% |
| MVP-0A | render + Stage 1 (1 cam) | 15-25 ms Stage 1 | 493-503 ms | 6-8% |
| MVP-0B | + Stage 0 + 2 cam | 2 ms Stage 0 + 25-40 ms Stage 1 | 505-520 ms | 8-11% |
| MVP-1 | + Stage 2 | +1-2 ms | 506-522 ms | 8-12% |
| MVP-2A | + Stage 3a surrogate | +3-5 ms | 509-527 ms | 9-12% |
| MVP-2B | + Stage 3 projection + refine | +15-30 ms (measured-TBD) | 524-557 ms | 11-17% |
| MVP-2C | + Stage 4 | <1 ms | 525-558 ms | 11-17% |
| MVP-3 | + augmented obs policy forward | +0.5 ms (forward dim 42→47 negligible) | 525-558 ms | 11-17% |

### 8.2 Budget rule (v3 explicit)

```text
Acceptable iff: camera_rendering_overhead + estimator_overhead <= 12% of step wallclock
Measured at: MVP-2B (all stages except aug-obs) and MVP-3 (all stages + policy)
Mitigation trigger: if moving-average Stage-3 wallclock over 100 steps > 30 ms → auto-enable:
  1. reduce estimator cadence
  2. restrict fit to routing-local window
  3. use previous-frame warm start exclusively
  4. full optimization → surrogate-only (degrade gracefully to MVP-2A level)
  5. defer obs replacement, keep sidecar-only
```

### 8.3 GPU slot + memory budget (v3 explicit, CC3-2/CC3-5)

- **cuda:0 (A6000 48GB, sim pool, max 4):** render stays here; estimator runs on cuda:2 (inference) or on cuda:0 if sim slot ratio allows
- **cuda:2 (PRO 4000 24GB, train pool, max 4):** MSA training + estimator training. At MVP-3, concurrent MSA + estimator inference must fit in 24 GiB with ≥ 2 GiB headroom (see §5.2 memory budget table)
- **Phase 5-1 contention (CC3-5):** MVP-0A recommended to run in **offline replay mode** (cuda:0 sim slot NOT required; cuda:2 slot 1 for segmenter training when Phase 5-1 slot available)

Any implementation ticket must include explicit GPU claim + process-slot plan + `/tmp/cc_gpu_claims.txt` CLAIM (per `cc_session_ssot_assignment_2026-04-25.md`).

### 8.4 Measured-benchmark gate (v3 new, CC3-1)

**Before OQ-1 approval:**

1. Implement candidate Stage 1 model (light U-Net 9-head)
2. Generate cached wrist RGB-D from 10 AC episodes (no concurrent Phase 5-1 cuda:2 load)
3. Replay through model on cuda:2 alongside concurrent MSA training load
4. Measure: p50, p99 latency, peak VRAM (fp16 inference)
5. Report: pass/fail against §5.2 memory budget and §8.1 MVP-0A target

Rs cannot approve OQ-1 (Option C-2R adoption + MVP-0A impl) without this measurement in hand. Skipping this gate = premature approval risk.

---

## 9. Validation strategy (v3 expanded)

### 9.1 Offline estimator metrics (unchanged from v2 + v3 additions)

| Metric | Definition | Gate |
| --- | --- | --- |
| Cable target position error | `||est_seg_pos - gt_seg_pos||` | < 5 mm @ MVP-2B |
| Cable target orientation error | quat angular distance | < 0.05 rad @ MVP-2B |
| Clip target position error | per-clip | < 3-5 mm @ MVP-2B |
| Clip orientation error | quat angular | task-dependent |
| Mask mIoU | per-class | > 0.8 cable / 0.75 clip @ MVP-0A |
| Jitter | frame-to-frame variance under static scene | must not destabilize error obs |
| Failure recovery | frames to recover after mask dropout | characterize before policy use |
| **[v3] Per-world isolation** (CC4-4) | reset world w → other worlds' prev_state unchanged | bit-equal unit test |
| **[v3] Quat convention** (CC4-6) | PoseEstimate14D.seg_quat_w matches Newton body_q[seg_idx, 3:7] | byte-for-byte over 100 random rotations |
| **[v3] R6 hard test** (CC5-1) | zero-visible-points → output = P(prior) not P(surrogate) | bit-comparable integration test |
| **[v3] Projection idempotency** (CC5-1) | P(P(x)) = P(x) | unit test |
| **[v3] FAIL_CLOSED timeouts** (CC4-2) | FAIL_CLOSED → dones=True, timeouts=False | integration test assert |
| **[v3] PREDICT_TEMPORAL bias** (CC4-3) | systematic bias of PREDICT output vs GT | `|mean_bias| < 0.5 mm / 0.005 rad` |
| **[v3] FALLBACK_NOMINAL_CLIP under DR forbidden** (CC5-3) | DR-on test: FALLBACK triggered when expected; obs never receives nominal | integration test with DR enabled |
| **[v3] Frame alignment** (CC3-6) | Stage 0 body_q id equals render body_q id | unit test |

### 9.2 Policy-level metrics (v3 AC-only for MVP-3)

| Skill | Test | When |
| --- | --- | --- |
| AC | success ≥ 90% of GT baseline over 100 eval episodes | MVP-3 |
| AR / Grip / IC | **deferred** pending §2.5 SSOT consolidation | MVP-4 post-decision |

### 9.3 Ablations (v3 expanded from v2)

| Ablation | Purpose |
| --- | --- |
| GT mask + Stage 2/3 | isolates segmentation error |
| pred mask + GT depth | isolates depth/projection error |
| pred mask + pred depth | full visual pipeline |
| one cam vs two cam | stereo-like coverage benefit |
| no temporal filter vs filter | jitter/recovery trade-off |
| routing-local fit (λ_roi > 0) vs full 40-seg fit (λ_roi = 0) | performance/accuracy trade-off + distribution-shift risk |
| no ROI vs Stage 0 ROI | routing-conditioned perception benefit |
| no self-occlusion vs self-occlusion mask | gripper/body FP reduction |
| surrogate only vs surrogate + hard projection | R6 projection contribution |
| confidence gate disabled vs enabled | silent-failure reduction |
| **[v3] NN mask_confidence vs physical proxy confidence** (CC5-9) | source-routing stability |
| **[v3] binary point weights vs soft weights** (CC5-4) | R6 residual-weight influence |
| **[v3] Cosserat-consistent vs linear IIR smoothing** (CC5-5) | predict-state accuracy |
| **[v3] arc-length monotonicity vs image-space monotonicity** (CC5-7) | tight-bend handling |
| **[v3] augmented 47D obs vs 42D shape-only** (CC5-2) | regime-awareness benefit |

### 9.4 Failure classification (v3 +1 new code)

| Code | Meaning |
| --- | --- |
| `SEG_EMPTY_CABLE` | cable mask missing/too small |
| `SEG_EMPTY_CLIP` | target clip mask missing/too small |
| `DEPTH_INVALID` | depth values invalid after mask |
| `FIT_DIVERGED` | cable/clip fit residual too high |
| `OCCLUDED_TARGET` | target occluded |
| `TEMPORAL_STALE` | prediction used beyond freshness |
| `ROUTING_MISMATCH` | target index inconsistent with estimator |
| `SEGMENT_SWAP` | arc-length monotonicity violation |
| `SURROGATE_INVALID` | DD-PINN proposal violates rod constraints before projection |
| `PROJECTION_FAILED` | constrained projection cannot reach tolerance |
| `CONFIDENCE_MISCALIBRATED` | high confidence but high residual |
| **[v3] `ROI_MISSED_CABLE`** (CC5-6) | ROI excluded true cable location |

Failure labels matter because the main risk is rare, unobserved failures entering policy input silently.

---

## 10. Risk register (v3 expanded with debate-surfaced risks)

| Risk | Severity | Why it matters | Mitigation | CHALLENGE Ref |
| --- | --- | --- | --- | --- |
| Cable target occluded by gripper | High | Policy receives stale/wrong target pose at precision phase | Temporal prior, two cameras, routing-local confidence, grip-specific validation | v2 §10 |
| Straight cable orientation degeneracy | Medium | Pos correct but quat unstable | Tangent smoothing, neighbor-derived orientation, confidence diagnostic | v2 §10 |
| Seg works in sim but not real | High | Stage 1 is main domain-gap surface | Domain randomization, light model first, real calibration later | v2 §10 |
| Estimator overhead breaks W=32 throughput | Medium | Slows RL iteration | Sidecar first, cadence control, routing-local fitting, surrogate degrade | v2 §10 |
| Mixed GT+est obs leak into training | High | Policy evaluation invalid | Integration test asserts all pose-dependent slices use same source | v2 §10 |
| Silent fallback hides estimator failure | High | Policy appears stable while estimator isn't solving | Mandatory diagnostics + failure counters | v2 §10 |
| Pure NN shortcut creeps into physical pose | Medium | R6 + interpretability violation | Restrict NN to seg unless Rs explicitly approves | v2 §10 |
| **[v3] DD-PINN domain mismatch** (continuum vs discrete 40-seg) | Critical | 2025 paper doesn't transfer; training dataset cost unscoped | PCA-tangent fallback; DD-PINN dataset gated pre-training | **CC3-3** |
| **[v3] Stage 1 U-Net budget exceeds target** | Critical | Estimator overhead > 12% budget | Measured benchmark pre-OQ-1; Fast-SCNN fallback | **CC3-1** |
| **[v3] IC-ObsReward-Misalignment replay** | Critical | IC env obs is 45D not 42D; uniform replacement reintroduces fixed bug | Per-skill contract table §1.1; IC deferred MVP-4 | **CC4-1** |
| **[v3] FAIL_CLOSED timeouts contamination** | Critical | value_loss 105x explosion replay | Explicit dones=T/timeouts=F rule §5.6 + integration test | **CC4-2** |
| **[v3] obs index arithmetic error** | Critical | 13D vs 14D off-by-one propagates through documentation and recomputation | §1.1 Python-slice explicit table; v3 §6.2 literal code form | **CC2-1 / CC3-8** |
| **[v3] AR penalty dominance replay** (PREDICT_TEMPORAL bias) | High | Systematic small error = hidden penalty bias | MVP-2C bias measurement gate; |mean_bias| < 0.5 mm | **CC4-3** |
| **[v3] RESET-EE per-world shared state** | High | Cross-world contamination silently breaks reset | Per-world isolation contract §5.1; unit test | **CC4-4** |
| **[v3] Collapsed checkpoint resume** (est-finetune from GT ckpt) | High | Obs distribution shift can cause collapse | Fresh-start rule: value_loss > 3× baseline → restart | **CC4-5** |
| **[v3] DD-PINN projection non-idempotent** | High | NN warm-start leaks into final pose, R6 violation | Hard idempotent P operator §5.4; regression test | **CC5-1** |
| **[v3] Stage 4 regime anonymity** (HARD R6) | High | Policy sees unmarked obs source change | Augmented obs 42D → 47D §6.4 | **CC5-2** |
| **[v3] FALLBACK_NOMINAL_CLIP under DR = lie** | High | R6 violation; obs is a known-wrong constant | Forbidden under DR §5.5; integration test | **CC5-3** |
| **[v3] Superficial contract preservation claim** | High | Misleads impl: shape preserved but semantics broken | Explicit contract break §2.4 | **CC5-8** |
| **[v3] Scipy CPU leak in Stage 0** | High | Current wrist_camera_manager scipy loop (~2 ms) cascades into Stage 0 | Warp kernel mandate §5.1; wrist_camera prereq | **CC3-4** |
| **[v3] GPU slot contention with Phase 5-1** | High | MVP-0A cannot run alongside 4 DAPG skills | Offline replay default §7.2 | **CC3-5** |
| **[v3] Stage 3a realistic 20-50 ms vs claimed 3-5 ms** | High | Budget breach at MVP-2B | Split surrogate vs projection+refine ms; measurement gate | **CC3-7** |
| **[v3] Confidence score unweighted / per-instance mismatch** | High | Stage 4 gates become arbitrary | Σw=1 constraint + per-object (cable/clip) decomposition §5.6 | **CC2-3** |
| **[v3] FAIL_CLOSED × error obs interaction undefined** | High | obs[30:42] recomputation under FAIL ambiguous | Explicit rule §6.2: last_accepted propagates through recomputation; regime bit notifies | **CC2-4** |
| **[v3] Memory cost missing** | High | cuda:2 budget overrun during MSA + estimator co-run | Memory budget table §5.2 + 2 GiB headroom rule | **CC3-2** |
| **[v3] Undefined operators in spec** (constraint projection / monotonicity / refinement) | High | Implementer guesses → spec drift | Operators specified §5.4 (hard projection, arc-length monotonicity, LM refinement) | **CC2-2** |
| **[v3] BC demo obs distribution mismatch** | Medium | Finetune on GT demos under est obs creates systematic action bias | Re-collect demos under noise OR BC loss equivalence check at MVP-3 | **CC4-8** |
| **[v3] Quat convention (xyzw vs wxyz) bug** | Medium | Silent frame mismatch → unit-norm but wrong rotation | Unit test byte-for-byte vs Newton body_q over 100 random rotations | **CC4-6** |
| **[v3] NN-soft point weights in Stage 3 residual** | Medium | NN output shapes physical fit — R6 soft violation | Binary weights (threshold > 0.5) in Stage 3 residual; soft weights only in diagnostics | **CC5-4** |
| **[v3] Smoothing IIR implicit dynamics model** | Medium | Non-physical temporal blending | Cosserat-consistent prediction for PREDICT; IIR only at ACCEPT+high-conf | **CC5-5** |
| **[v3] Stage 0 ROI leakage** (wrong prior excludes true cable) | Medium | NN-era prior shapes physical search space | λ_roi = 0 during distribution-shift eval; rollback gate; ROI_MISSED_CABLE failure code | **CC5-6** |
| **[v3] Image-space monotonicity vs arc-length** | Medium | Tight bends falsely pulled straight | Arc-length Cosserat monotonicity §5.4 | **CC5-7** |
| **[v3] NN mask_confidence routes obs source in Stage 4** | Medium | NN decides physical source of truth | Physical proxies replace NN confidence in gate §5.6 | **CC5-9** |
| **[v3] obs[30:42] R6 exposure multiplication** | Low | ~24D of policy obs influenced by estimator, not just 14D | §6.2 disclosure + regime-aware training | **CC5-10** |
| **[v3] Symbol W overloaded** (worlds vs image width) | Medium | Reader confusion | §3.2 uses B for world batch, H_img/W_img for image | **CC2-6** |
| **[v3] DD-PINN convergence basin undefined** | Medium | MVP-2A exit criteria ambiguous | Basin: 10 LM iters reduce residual ≥ 90% §5.4 | **CC2-7** |
| **[v3] MVP-0A auxiliary heads not gated** | Low | depth_valid/occlusion could be garbage at MVP-0A gate | AUROC gate added §7.1 | **CC2-8** |
| **[v3] Confidence scalar units unspecified** | Low | AGENTS.md SI units rule | Dataclass docstring §3.2 specifies SI units | **CC4-9** |
| **[v3] Kinematic trick fallback risk** | Medium | Future impl might read body_q as fallback = forbidden | Explicit §10 entry + integration test greps estimator for `newton.*body_q` | **CC4-7** |
| **[v3] Per-skill AR / Grip obs contract unverified** | Medium | Currently assumed = 42D per RL-Routing-Design but IC diverges; AR/Grip may too | §2.5 SSOT consolidation prerequisite to MVP-4 | **CC4-1 extension** |

---

## 11. Open decisions for Rs (v3 revised)

### OQ-1: Option approval (Measured-benchmark gate added)

```text
Approve Option C-2R as target design.
PREREQUISITE: Stage 1 measured benchmark (§8.4) must be produced and pass §5.2 memory budget + §8.1 MVP-0A latency target before C-2R adoption is final.
```

Alternative decisions:

- Option A if implementation speed over precision/occlusion robustness
- Option B if R6 explicitly relaxed
- Option D as later refinement or offline oracle
- v2 C-2 if v3 ROI/confidence/fallback machinery considered too much

### OQ-2: MVP scope (unchanged from v2 statement, AC-only for MVP-3)

```text
Approve staged MVP-0A → MVP-0B → MVP-1 → MVP-2A/B/C → MVP-3 (AC-only).
MVP-4 (IC/AR/Grip) is DEFERRED pending OQ-5 SSOT consolidation.
```

### OQ-3: Implementation timing (revised for GPU slot reality)

```text
Keep design parked until Phase 5-1 / current RL priorities clear OR Vision Stack un-parked.
MVP-0A may run ONLY in offline replay mode (no cuda:0 sim slot contention) if cuda:2 slot is available;
MUST NOT run alongside 4 DAPG skills.
```

### OQ-4: DR noise distribution (unchanged)

```text
Use placeholder noise only for early robustness experiments; set final DR noise from measured
estimator residuals at MVP-2B.

Initial placeholder:
  sigma_pos = 3 mm
  sigma_ori = 0.03 rad

Hard rule: MVP-3 integration must calibrate DR noise from MVP-2B measured residuals;
placeholder values must not be frozen as design truth.
```

### OQ-5: Per-skill obs SSOT consolidation (v3 new, MVP-4 blocker)

```text
Decide per-skill obs contract consolidation strategy:
  (A) Unify all 4 skills to RL-Routing-Design 42D (IC env refactor required)
  (B) Maintain per-skill obs; estimator has per-skill output heads (default assumed)
  (C) Defer IC entirely from pose estimation integration (keep IC on GT obs permanently)

This decision blocks MVP-4 but not MVP-0A~3.
Current fact: IC env is 45D groove-relative (verified newton_insert_clip_env.py:1165-1181),
differs from RL-Routing-Design.md §4 "common 42D" spec.
AR and Grip obs contracts require independent verification before MVP-4.
```

### OQ-6: Sim-to-real PoC timing (unchanged from v2)

```text
Defer real-robot PoC until MVP-4 OR Vision Stack Roadmap un-parked.
```

---

## 12. Implementation checklist (v3 expanded)

Before any code lands:

- [ ] OQ-1 approved + Stage 1 measured benchmark passed
- [ ] OQ-2 MVP-0A scope only
- [ ] OQ-3 offline replay mode (no cuda:0 sim slot contention)
- [ ] OQ-4 initial placeholder noise acceptable for pre-MVP
- [ ] OQ-5 deferred IC (MVP-4 scope)
- [ ] GPU claim registered in `/tmp/cc_gpu_claims.txt`
- [ ] Synthetic sim-label source confirmed (Isaac Sim semantic seg API verified)
- [ ] wrist_camera_manager scipy-loop refactor status confirmed (if still on scipy, Stage 0 Warp kernel must wrap)
- [ ] AC env obs layout grep-verified at impl time (not assumed from this doc)
- [ ] Dataset generation command reproducible
- [ ] Output artifact format agreed (visualizations, mIoU, ROI recall, AUROC)

Before env integration (MVP-3):

- [ ] MVP-0A ROI + mask gate passed
- [ ] MVP-0B two-cam + self-occlusion gate passed
- [ ] MVP-1 point-cloud gate passed
- [ ] MVP-2A surrogate warm-start basin test passed
- [ ] MVP-2B projection/refinement + R6 hard test + idempotency test + quat convention test passed
- [ ] MVP-2C confidence/fallback + FAIL_CLOSED timeouts test + PREDICT_TEMPORAL bias test passed
- [ ] Per-world isolation unit test passed
- [ ] Estimator never imports newton.body_q for seg_pos computation (grep lint)
- [ ] Error obs recomputation path confirmed bit-equivalent to env helper semantics
- [ ] Diagnostics emitted and logged (11 failure codes + regime state)
- [ ] Fallback behavior is explicit and counted
- [ ] GT-vs-est source mixing test passes (no GT leaks into est training)
- [ ] AC env obs layout verified as 42D (fail loud if different)

Before policy fine-tuning (MVP-3):

- [ ] Offline estimator residual distribution characterized (MVP-2B measurement complete)
- [ ] DR noise distribution set from measured residuals
- [ ] AC-only integration tested
- [ ] Baseline GT observation AC run re-confirmed (baseline at or above target)
- [ ] Estimator-on AC policy finetune initiates from converged GT checkpoint
- [ ] Fresh-start rollback rule active: value_loss > 3× baseline at 20 iters → restart
- [ ] BC demos: either re-collected under noise OR BC loss equivalence check (noisy vs GT BC loss within 2×)
- [ ] Augmented obs (47D) implemented; policy head dim updated from 42 to 47
- [ ] Training logs regime frequency, not only mean error

---

## 13. Revised document status (v3)

This v3 version incorporates the 5-CC Debate outcomes (2026-04-25):

- CC2 General Technical Auditor: 8 challenges (1 CRITICAL, 3 HIGH, 3 MEDIUM, 1 LOW)
- CC3 Training Infrastructure: 8 challenges (2 CRITICAL, 4 HIGH, 2 MEDIUM)
- CC4 Past-Failure Replay: 9 challenges + 9 past bugs replayed (2 CRITICAL, 3 HIGH, 3 MEDIUM, 1 LOW)
- CC5 R6 / SUBLIMATE: 10 challenges (0 CRITICAL, 4 HIGH, 5 MEDIUM, 1 LOW)
- CC6 NHA: HOLD_WITH_CAVEATS / NO_ACTION_RECOMMENDED (Rs over-ridden via Option X2)

v3 addresses all 5 CRITICAL + 14 HIGH challenges (per Rs X2 directive). Selected MEDIUM/LOW addressed where cost is low (bundled with related HIGH fixes). Remaining MEDIUM/LOW tracked in §10 risk register.

Key v3 deltas from v2:

- per-skill obs contract table (§1.1) with IC verified 45D divergence from "common 42D"
- MVP-4 deferred pending §2.5 + OQ-5 SSOT consolidation
- measured-benchmark gate for Stage 1 (§8.4, OQ-1 prerequisite)
- hard idempotent projection operator (§5.4)
- binary point weights in Stage 3 residual (§5.3)
- physical-proxy confidence in Stage 4 gate (§5.6, not NN output)
- augmented obs 42D → 47D for AC MVP-3 (§6.4)
- FAIL_CLOSED dones=True/timeouts=False explicit rule (§5.6, §6.2)
- FALLBACK_NOMINAL_CLIP forbidden under DR (§5.5)
- arc-length monotonicity (not image-space) (§5.4)
- Cosserat-consistent smoothing for PREDICT (not linear IIR) (§5.6)
- per-world isolation contract (§5.1, §9.1)
- offline replay default for MVP-0A (§7.2)
- Warp kernel mandate for Stage 0 (§5.1)
- expanded risk register with 35 entries (§10)
- expanded implementation checklist (§12)
- debate traceability (Appendix C, new)

The design remains a **proposal**. The next action is Rs approval on OQ-1 (with measured benchmark) + OQ-5 (SSOT consolidation strategy).

---

## Appendix A: Glossary (v3 expanded)

| Term | Meaning |
| --- | --- |
| MSA | Multi-Skill Agent, 42D-obs / 12D-action policy stack across AC, IC, AR, Grip |
| VBD | Vertex Block Descent, Newton solver path used for cable |
| DLO | Deformable Linear Object |
| DR | Domain Randomization |
| DAPG | Demo Augmented Policy Gradient |
| R6 | SUBLIMATE Observation Grounding rule: learned decoding allowed, but physical quantities must remain physically constrained |
| ICP | Iterative Closest Point |
| DD-PINN | Domain-Decoupled Physics-Informed Neural Network |
| GT | Ground truth; here simulator state such as Newton body_q |
| B | Number of parallel worlds (used in tensor shapes to avoid W overload with image width) |
| W | Parallel worlds (narrative only) / image width (tensor shape only, suffixed `_img`) |
| C | Number of cameras |
| ROI | Region of Interest |
| NHA | Null Hypothesis Advocate (CC Debate role) |
| LM | Levenberg-Marquardt optimizer |
| PCA | Principal Component Analysis (used for analytic tangent warm-start) |
| SI units | position: m, orientation: rad, residual: mm, confidence: dimensionless |
| FOV | Field of View |

## Appendix B: Source lineage (v3)

v3 consolidates and extends v2 and v1, incorporating:

- Vision Pipeline / R6 observation grounding (vault)
- Camera Backend precedent (vault)
- Vision Stack Roadmap (vault, Parked)
- DLO Research Survey (vault, 2025-2026 DLO)
- LL-VisualObs-CameraSystem camera benchmark (vault)
- RL-Routing-Design observation contract (vault, §4)
- THREAD-specific Newton VBD + MSA constraints (CLAUDE.md + task_config.py)
- newton_insert_clip_env.py:1165-1181 (2026-04-25 verification: IC is 45D)
- newton_approach_cable_env.py:1253-1301 (AC env 42D absolute quat confirmation)

External research (from v2, retained):

- [Deep Learning-Based Object Pose Estimation: A Comprehensive Survey](https://github.com/CNJianLiu/Awesome-Object-Pose-Estimation)
- [GoTrack: Generic 6DoF Object Pose Refinement and Tracking](https://github.com/facebookresearch/gotrack)
- [Pose-Perceptive Convolution](https://pmc.ncbi.nlm.nih.gov/articles/PMC12845661/)
- [Enhanced RGB-D Feature Extraction for 6D Pose Estimation](https://www.nature.com/articles/s41598-025-34757-y)
- [R3M: A Universal Visual Representation](https://openreview.net/forum?id=tGbpgz6yOrI)
- [Adaptive MPC of Soft Continuum Robot using PINN + Cosserat](https://arxiv.org/html/2508.12681v1)
- [Cosserat Rods / Elastica](https://www.cosseratrods.org/)
- [DREAM Camera-to-Robot Pose](https://www.ri.cmu.edu/app/uploads/2020/03/dream_icra2020_final.pdf)
- [Training-Free Robot Pose Estimation](https://arxiv.org/html/2512.06017v1)

## Appendix C: Debate response traceability (v3 new)

This appendix records each v2-debate CHALLENGE → v3 response for auditability.

### C.1 CRITICAL (5 items)

| CHALLENGE | Agent | Severity | v3 Resolution | Section |
| --- | --- | --- | --- | --- |
| obs index arithmetic 13D vs 14D | CC2-1 / CC3-8 | CRITICAL | §1.1 per-skill table with Python slice + inclusive; 14D confirmed | §1.1, §6.2 |
| Stage 1 U-Net budget unmeasured | CC3-1 | CRITICAL | Measured benchmark gate added pre-OQ-1; §5.2 memory budget; Fast-SCNN fallback | §5.2, §8.4 |
| DD-PINN domain mismatch (continuum vs discrete) | CC3-3 | CRITICAL | Applicability note + dataset cost scope + PCA-tangent fallback | §5.4 "DD-PINN surrogate applicability note" |
| IC-ObsReward-Misalignment replay (per-skill contract) | CC4-1 | CRITICAL | Per-skill contract table; IC 45D verified; MVP-4 deferred | §1.1, §2.5, §7.1 |
| FAIL_CLOSED timeouts contamination | CC4-2 | CRITICAL | Explicit dones=True/timeouts=False rule + integration test | §5.6, §6.2, §9.1 |

### C.2 HIGH (14 items)

| CHALLENGE | Agent | Severity | v3 Resolution | Section |
| --- | --- | --- | --- | --- |
| Undefined operators | CC2-2 | HIGH | Hard projection + arc-length monotonicity + LM refinement specified | §5.4 |
| Confidence score weights + per-instance | CC2-3 | HIGH | Σw=1 + default weights + per-object decomposition | §5.6 |
| FAIL_CLOSED × error obs interaction | CC2-4 | HIGH | last_accepted propagation + regime bit to policy | §5.6, §6.2 |
| Memory cost missing | CC3-2 | HIGH | Memory budget table with 2 GiB headroom rule | §5.2 |
| Scipy CPU leak inherited by Stage 0 | CC3-4 | HIGH | Warp kernel mandate + wrist_camera prereq | §5.1 |
| OQ-3 parallel to Phase 5-1 false | CC3-5 | HIGH | Offline replay default | §7.2, §8.3 |
| Stage 3a 20-50ms not 3-5ms | CC3-7 | HIGH | Split surrogate vs projection+refine estimates; MVP-2B measurement gate | §8.1 |
| AR penalty dominance replay (PREDICT bias) | CC4-3 | HIGH | §10 risk + MVP-2C bias gate | §9.1, §10 |
| RESET-EE per-world isolation | CC4-4 | HIGH | Per-world isolation contract + unit test | §5.1, §9.1 |
| Collapsed checkpoint resume | CC4-5 | HIGH | Fresh-start rollback rule | §7.1 MVP-3, §12 |
| DD-PINN projection non-idempotent | CC5-1 | HIGH | Hard idempotent P operator + regression test | §5.4 |
| Stage 4 regime anonymity (HARD R6) | CC5-2 | HIGH | Augmented obs 42D → 47D | §2.4, §6.4 |
| FALLBACK_NOMINAL_CLIP under DR = lie | CC5-3 | HIGH | Forbidden under DR + integration test | §5.5 |
| Superficial contract preservation | CC5-8 | HIGH | Contract break disclosure §2.4 | §2.4 |

### C.3 MEDIUM (13 items, selected addressed, rest in risk register §10)

| CHALLENGE | Agent | v3 Status |
| --- | --- | --- |
| Perf budget per-MVP missing | CC2-5 | Addressed §8.1 |
| Symbol W overload | CC2-6 | Addressed §3.2 (B for batch, W_img for image) |
| DD-PINN convergence basin | CC2-7 | Addressed §5.4 (10 LM iters, ≥90% residual reduction) |
| Frame alignment body_q(t) | CC3-6 | Addressed §5.1 |
| obs index arithmetic duplicate | CC3-8 | Addressed §1.1 |
| Quat convention bug | CC4-6 | Addressed §9.1 regression test |
| Kinematic trick fallback risk | CC4-7 | Addressed §10 + §12 grep lint |
| BC demo mismatch | CC4-8 | Addressed §12, §7.1 MVP-3 |
| NN-soft point weights | CC5-4 | Addressed §5.3 (binary weights) |
| Smoothing IIR | CC5-5 | Addressed §5.6 (Cosserat for PREDICT) |
| Stage 0 ROI leakage | CC5-6 | Addressed §5.4 (λ_roi=0 for eval), §9.4 ROI_MISSED_CABLE |
| Image-space monotonicity | CC5-7 | Addressed §5.4 (arc-length) |
| NN mask_confidence gates Stage 4 | CC5-9 | Addressed §5.6 (physical proxies) |

### C.4 LOW (3 items)

| CHALLENGE | Agent | v3 Status |
| --- | --- | --- |
| MVP-0A auxiliary head gates | CC2-8 | Addressed §7.1 (AUROC gates) |
| Confidence scalar units | CC4-9 | Addressed §3.2 SI units in docstring |
| obs[30:42] R6 exposure multiplication | CC5-10 | Addressed §6.2 disclosure |

### C.5 NHA (CC6)

| Claim | Rs decision | v3 position |
| --- | --- | --- |
| NULL_HYPOTHESIS: HOLD_WITH_CAVEATS (keep v1 stock + minimal v2 appendix) | Rs Option X2 (adopt v2 + v3 revision, over-ride NHA) | v3 honors X2; NHA recommendations re-frame as safety considerations: scoping to AC-only MVP-3 + parking status until Rs authorizes + OQ-5 IC deferral |

### C.6 Additional verified finding (post-debate)

| Discovery | Impact | v3 Action |
| --- | --- | --- |
| IC env 45D obs ≠ 42D common spec | MVP-4 scope blocker | §2.5 SSOT consolidation prerequisite + OQ-5 |

---

**v3 status:**

- ✅ All 5 CRITICAL challenges addressed (§1.1, §2.5, §5.2, §5.4, §5.6, §8.4)
- ✅ All 14 HIGH challenges addressed (§2.4, §5.1-5.6, §6.1-6.4, §7, §8, §10, §12)
- ✅ Selected 13 MEDIUM addressed (§3.2, §5.1, §5.4, §5.6, §7.1, §9, §10, §12)
- ✅ All 3 LOW addressed (§3.2, §6.2, §7.1)
- ✅ IC 45D finding documented (§1.1, §2.5)
- ✅ Debate traceability Appendix C
- 🔵 **Rs approval pending** for OQ-1 (with measured benchmark) + OQ-2 + OQ-3 + OQ-5

**Next action:** Rs decision on the 5 OQs. If approved, MVP-0A impl starts via new CC session with GPU claim registered.

---

**Cross-references:**

- v1 (superseded): `thread-vault/07-Design/PoseEstimation-Design-v1.md`
- v2 (Rs improvement): `thread-vault/07-Design/PoseEstimation-Design-v2.md` + `/home/rlrk/Downloads/pose-estimation-design-v2.md`
- Downloads copies: `/home/rlrk/Downloads/PoseEstimation-Design-v1.md`、v2、v3 (to be copied)
- Debate record (5 agents): session 2026-04-25 CC#4 chat log
- Handoff: `memory/handoff_cc4_pose_estimation.md`
- Memory pointer: `memory/project_pose_estimation_design_v1.md` (to be updated for v3)
- Log milestone: `thread-vault/log.md` (to be appended)
- Pending index: `memory/_pending_index.txt` (to be appended for v3)
