---
status_ledger: 00-DESIGN-STATUS-LEDGER.md  # authoritative success/failure status SSOT
title: Pose Estimation Design v3.1 — Patch to v3 (12 improvements, 5 essential + 7 supporting)
created: "2026-04-25T07:30:00+09:00"
updated: "2026-04-25T07:30:00+09:00"
status: "Patch — supersedes v3 for sections listed below; unchanged sections inherit v3"
owner: "CC#4 / Pose Estimation Research"
supersedes: "[[PoseEstimation-Design-v3]] (sections listed in §1.2)"
parent: "[[PoseEstimation-Design-v3]]"
rs_directive: "Rs 2026-04-25 feedback list — 12 improvements, 5 essential for v3.1 patch (inputs whitelist / OQ-1 split / 47D migration / projection tolerance / dataset split)"
tags:
  - design
  - vision
  - pose-estimation
  - patch
  - post-debate-refinement
---

# Pose Estimation Design v3.1 — Patch to v3

> **⚠ PARTIAL SUPERSEDE — renewal batch B, 2026-07-11 (banner-only; content edit-frozen):** this patch is **superseded by v3.2 only for the sections listed in v3.2 §1.2** (`00-DESIGN-STATUS-LEDGER.md:51` = 🔁 **SUPERSEDED** → v3.2). This is **not** a whole-document archive: sections **not** listed in v3.2 §1.2 remain **normative** as a constituent of the composite head. Read as part of the head stack — **open v3 + v3.1 + v3.2 together** (v3.2 §1.1). Current head: `[[PoseEstimation-Design-v3.2]]` (`:50`, PARKED/unvalidated). Status SSOT = `00-DESIGN-STATUS-LEDGER.md`.

## 1. Patch scope

### 1.1 Parent doc

v3.1 is a **patch** to `PoseEstimation-Design-v3.md`. Read v3 first; this document modifies only the sections listed below. Unchanged sections retain their v3 specification.

### 1.2 Sections modified in v3.1

| Patch ID | v3 Section affected | Change | Priority |
| --- | --- | --- | --- |
| P1 | §11 OQ-1 | Split into OQ-1a (concept) + OQ-1b (impl gate) | **Rs essential** |
| P2 | §3.2 + Appendix D (NEW) | Allowed / Forbidden estimator inputs + API type separation | **Rs essential** |
| P3 | Appendix E (NEW) + §6 (new §6.5) | 42D → 47D policy migration + normalizer migration + zero-init adapter | **Rs essential** |
| P4 | §5.4 + §9.1 + Appendix G (NEW) | Projection test tolerance: CPU fp64 idempotent vs GPU fp32/fp16 approximate | **Rs essential** |
| P5 | §7.1 MVP-0A + Appendix F (NEW) | Dataset split protocol by episode seed, held-out randomization, occlusion strata | **Rs essential** |
| P6 | §5.6 Stage 4 + §6.2 + §9.1 | FAIL_CLOSED explicit obs content (moved up from MVP-2C TBD) | supporting |
| P7 | §5.6 + §9.2 | FAIL_CLOSED training vs eval semantics separation | supporting |
| P8 | §7.1 MVP-2C + §9.1 | Confidence evaluation expanded (AUROC + high-conf bad rate + calibration) | supporting |
| P9 | §5.3 | Binary threshold selected on validation + per model version | supporting |
| P10 | §5.3 | Normalized visible_point_ratio gate alongside absolute count | supporting |
| P11 | §7.1 MVP-0B+ | Passive cross-skill RGB-D replay (AR/Grip/IC visibility report, no integration) | supporting |
| P12 | §5.4 + §7.1 MVP-2A | Warm-start priority: prev_state → analytic PCA → DD-PINN candidate | supporting |

### 1.3 Rs directive record

Rs 2026-04-25 feedback: "改善余地はありますが、設計方針を変える必要はありません。現在の v3 は (C-2R / AC-only / MVP-4 deferred / 47D augmented obs / hard projection / fallback visible to policy) で十分に強い。次の一手は、設計をさらに長くするより、以下の 5点だけを v3.1 patch として足す。"

v3.1 honors the directive: patch form, 5 essentials fully specified (+ 7 supporting for minimum additional implementation safety).

---

## 2. P1 — OQ-1 two-stage split (§11 replacement)

**v3 §11 OQ-1** had a circular dependency: "Stage 1 measured benchmark must pass before OQ-1 approval", but benchmark production itself requires prior CC permission to implement candidate models + replay scripts.

**v3.1 replacement:**

### OQ-1a: Concept approval

```text
Approve Option C-2R as the target design direction.

Approval grants CC permission to:
- set up offline replay framework
- implement candidate Stage 1 model (light U-Net or Fast-SCNN)
- generate MVP-0A sim-label dataset
- produce measured benchmark for Stage 1 latency / memory / quality

Approval does NOT grant:
- env obs replacement
- policy integration / fine-tuning
- cuda:0 sim slot usage (offline replay only)
- MVP-2 and beyond
```

### OQ-1b: Implementation gate (post-benchmark)

```text
Approve MVP-0A full implementation + subsequent MVPs.

Prerequisite: Stage 1 measured benchmark must pass:
- latency p50 <= 20 ms, p99 <= 35 ms at B=32, C=2, 128 (fp16 inference on cuda:2 alongside MSA training load)
- memory VRAM <= 3 GiB inference (+ 2 GiB headroom on cuda:2 24 GiB)
- quality mIoU cable > 0.8, clip > 0.75, ROI recall > 0.95
- (see Appendix G for numerical tolerance details)

Rs authorizes MVP-0B, MVP-1, MVP-2A/B/C, MVP-3 in sequence only after OQ-1b approval.
```

This removes the CC-blocks-on-benchmark-permission loop. MVP-0A work is gated on OQ-1a (available now). MVP integration is gated on OQ-1b (available after benchmark).

---

## 3. P2 — Estimator Input Boundary (new Appendix D + §3.2 patch)

v3 forbids kinematic-trick fallback but does not cleanly separate **allowed body/state usage** (arm joint state, wrist camera pose, finger geometry) from **forbidden body/state usage** (cable body_q as estimator output, GT clip pose, target seg GT).

See **Appendix D** (below) for full specification. Summary:

### 3.1 Allowed inputs (estimator may consume)

- wrist RGB-D tensors
- camera intrinsics / extrinsics (derivable from robot kinematics)
- arm joint position / velocity
- wrist camera body pose (computed from body_q at wrist link)
- gripper / finger geometry (for self-occlusion projection)
- routing target indices (cable seg index, clip index)
- previous estimator state (self-output, not GT)

### 3.2 Forbidden inputs (MUST NOT flow into estimator output)

- cable `body_q[target_seg_idx]` — this IS the GT we are replacing
- clip GT pose under DR — DR makes nominal wrong; using it = R6 lie (CC5-3)
- any Newton state for object pose (cable, clip) — except labels for **offline evaluation only** (§Appendix D API)
- future-frame state (no oracle look-ahead)
- reward / success internals (§ no reward-hacking surface)

### 3.3 API type separation (v3.1 patch to v3 §3.2)

```python
from dataclasses import dataclass
import torch

@dataclass
class EstimatorInputs:
    """ONLY these enter PoseEstimatorV1.forward()."""
    rgb_l: torch.Tensor           # [B, 3, 128, 128]
    rgb_r: torch.Tensor
    depth_l: torch.Tensor         # [B, 1, 128, 128]
    depth_r: torch.Tensor
    joint_state: torch.Tensor     # [B, J] arm joint pos + vel
    wrist_camera_pose_l: torch.Tensor   # [B, 7] derivable from body_q[wrist_L]
    wrist_camera_pose_r: torch.Tensor
    gripper_geometry_l: torch.Tensor    # [B, G, 3] static finger mesh in world frame
    gripper_geometry_r: torch.Tensor
    routing_target_seg_idx: torch.Tensor   # [B] int
    routing_target_clip_idx: torch.Tensor  # [B] int
    previous_estimate: PoseEstimate14D | None    # self-referenced only


@dataclass
class EstimatorLabelsForEvalOnly:
    """GT labels for OFFLINE EVALUATION ONLY.

    Must NOT be passed to PoseEstimatorV1.forward().
    Compile-time-enforced separation.
    """
    gt_cable_body_q: torch.Tensor    # [B, 40, 7]
    gt_clip_pose: torch.Tensor       # [B, 5, 7]
    gt_target_seg_idx: torch.Tensor  # [B]


def enforce_eval_label_isolation(estimator_fn):
    """Decorator asserts estimator_fn signature contains no GT body_q field.
    Runtime check at module import time.
    """
    sig = inspect.signature(estimator_fn)
    for param_name in sig.parameters:
        if 'body_q' in param_name.lower() or 'gt_' in param_name.lower():
            raise TypeError(
                f"Estimator function '{estimator_fn.__name__}' "
                f"cannot accept GT-like parameter '{param_name}'. "
                f"See Appendix D for allowed inputs."
            )
    return estimator_fn


class PoseEstimatorV1:
    @enforce_eval_label_isolation
    def forward(self, inputs: EstimatorInputs) -> PoseEstimate14D:
        # ...
        pass


class EvalPoseEstimator:
    def compare(
        self,
        estimate: PoseEstimate14D,
        labels: EstimatorLabelsForEvalOnly,
    ) -> dict:
        # Only place where GT and estimate coexist.
        pass
```

Integration test (v3.1 required for MVP-0A):

```python
def test_no_gt_in_estimator():
    """grep estimator module source for forbidden patterns."""
    estimator_module_source = read_source('thread_isaac_lab/estimators/')
    forbidden_patterns = [
        r'\.body_q\[',            # no direct Newton body_q access
        r'body_q\[.*target_seg',  # no target seg GT extraction
        r'GROOVE_TARGET',         # no GT clip pose access
        r'self\._state.*body_q',  # no sim state bypass
    ]
    for pat in forbidden_patterns:
        assert not re.search(pat, estimator_module_source), \
            f"Estimator module contains forbidden pattern: {pat}"
```

### 3.4 Rationale

**Implementer who accidentally passes `cable body_q` to estimator breaks the entire design** (estimator would be "learning" from oracle state, not from sensors → R6 violation + sim-to-real transfer broken). Type-level + grep-level enforcement prevents this drift.

---

## 4. P3 — 42D → 47D policy migration (new Appendix E + §6.5)

v3 correctly discloses the 42D → 47D contract break but does not specify the migration procedure. v3.1 adds concrete procedure to reduce MVP-3 checkpoint collapse risk.

See **Appendix E** (below) for full specification. Summary:

- **Obs normalizer migration**: inherit old 42D running mean/std, initialize new 5D
  - ACCEPT one-hot init: mean = [1, 0, 0, 0], std = epsilon (~0.01)
  - confidence init: mean = 1.0, std = epsilon
- **Network first-layer weight migration**: copy old 42D weights, **zero-init** new 5D weights
  - `W_new[:, :42] = W_old` (copy)
  - `W_new[:, 42:47] = 0` (zero-init)
  - `b_new = b_old` (unchanged)
- **Initial behavior guarantee**: at training step 0, 47D policy output matches 42D policy output exactly (since zero-init contributes 0 to activations under ACCEPT regime + confidence = 1.0)
- **Rollback criterion**: value_loss > 3 × baseline end-of-training value_loss at 20 finetune iters → fresh start from GT-obs baseline checkpoint + re-apply migration

This procedure is explicitly specified in Appendix E.

---

## 5. P4 — Projection test tolerance (new Appendix G + §5.4 + §9.1 patch)

v3 §5.4 mandates bit-comparable idempotency test `P(P(x)) = P(x)`. v3.1 relaxes to **two-tier** testing:

### 5.1 Mathematical idempotency (CPU, deterministic)

- Platform: CPU fp64 numpy with fixed random seed
- Tolerance: 1e-10 to 1e-8 (position in m, quaternion angular)
- Purpose: verify projection operator is mathematically correct
- Required test case: random q_0, q_1 = P(q_0), q_2 = P(q_1) → assert max(|q_1 - q_2|) < 1e-10

### 5.2 Implementation approximate idempotency (GPU, realistic)

- Platform: cuda:0 / cuda:2, fp32 or fp16 mixed precision allowed
- Tolerance:
  - position difference: < 1e-5 m (= 0.01 mm)
  - quaternion angular difference: < 1e-5 rad
  - constraint residual non-increasing across projection iterations
- Purpose: verify production implementation preserves projection contract under numerical reality
- Not required: bit-equivalence

See **Appendix G** (below) for full specification.

### 5.3 v3 §5.4 patch (idempotency block replacement)

Replace v3 §5.4 "Idempotency test":

```text
Idempotency test (unit test required):
  input q' = P(q0) for arbitrary q0
  assert P(q') == q' within 1e-8 tolerance
```

with v3.1 version:

```text
Idempotency test (two-tier, both required for OQ-1b):

  CPU deterministic:
    fp64, fixed seed
    P(P(q0)) - P(q0) max absolute < 1e-10 (position m)
    quaternion angular distance < 1e-10 rad

  GPU integration (at production precision):
    fp32 or mixed fp16 permitted
    ||P(P(q0)) - P(q0)||_pos < 1e-5 m
    ||P(P(q0)) - P(q0)||_quat_angular < 1e-5 rad
    constraint_residual(P(q0)) <= constraint_residual(q0) * 1.01

  R6 hard test (same as v3, unchanged):
    zero-visible-points scenario → output bit-comparable to prior-only projected
    (NOT influenced by DD-PINN warm-start content, measured at CPU fp64)
```

---

## 6. P5 — Dataset split protocol (new Appendix F + §7.1 MVP-0A patch)

v3 MVP-0A exit gate only specifies aggregate mIoU. v3.1 adds strict dataset split + per-stratum reporting to avoid train/test leak + hidden occlusion regime failures.

See **Appendix F** (below) for full specification. Summary:

- **Split by episode seed**, not by frame (continuous-frame leakage forbidden)
- **Held-out randomization** in test set: lighting / cable shape / camera noise / clip DR are OOD vs train
- **Occlusion strata**: normal / partial / heavy gripper / low mask area / high background — reported separately
- **Per-stratum metrics**: mIoU per stratum, not only aggregate
- **Failure subset**: grip-like occlusion sub-report

v3 MVP-0A exit gate is patched to require:

```text
Aggregate: mIoU cable > 0.8, clip > 0.75 (UNCHANGED from v3)
Per-stratum (v3.1 ADDITION):
  normal: mIoU > 0.85
  partial occlusion: mIoU > 0.75
  heavy gripper occlusion: mIoU > 0.65
  low mask area (object < 2% of frame): mIoU > 0.60
  high background clutter: mIoU > 0.75
Aggregate ROI recall: > 0.95 (UNCHANGED)
Per-stratum ROI recall: > 0.85 for heavy gripper occlusion stratum
```

---

## 7. P6 — FAIL_CLOSED explicit obs content (§5.6 + §6.2 patch)

v3 §5.6 defers FAIL_CLOSED obs content to MVP-2C ("last accepted pose or zero-filled with flag — to be decided Rs"). This is too late: replay dataset / policy input normalization / value target / terminal transition handling all depend on the decision. **v3.1 decides now**:

### 7.1 FAIL_CLOSED obs content (v3.1 decision)

```python
def on_fail_closed(world_idx):
    # Episode termination mapping (v3 rule retained)
    dones[world_idx] = True
    extras["time_outs"][world_idx] = False

    # v3.1 obs content decision (replaces v3 "TBD"):
    obs[world_idx, 16:30] = last_accepted_pose[world_idx]       # 14D: last accepted visual estimate
    obs[world_idx, 30:42] = recompute_error(                    # 12D: recomputed error from last_accepted
        hand_state[world_idx],
        last_accepted_pose[world_idx],
    )
    obs[world_idx, 42:46] = [0, 0, 0, 1]                        # one-hot FAIL_CLOSED
    obs[world_idx, 46] = 0.0                                    # confidence = 0

    # Diagnostics
    diagnostics.failure_code[world_idx] = FAIL_CLOSED_CODE
    diagnostics.used_prediction[world_idx] = False
    # (used_prediction only for PREDICT_TEMPORAL regime)
```

### 7.2 Rationale — why last_accepted, not zero-fill

Zero-filled obs would carry a **physically-meaningful** value (pose = 0, which is a specific location and orientation). Policy and value network could learn `obs ≈ 0 → episode ending`, coupling terminal handling to estimator pathology. This creates:

- Terminal obs distribution mismatch: policy sees "origin pose" only at FAIL_CLOSED, biasing value at origin
- Training-time leakage: if estimator failure mode correlates with scene state, zero obs at termination biases value estimates for similar non-failure states

Using **last_accepted** pose:
- Preserves physical sensibility of obs (policy sees plausible pose)
- Combined with regime bit `obs[45] = 1.0` (one-hot FAIL_CLOSED) + confidence `obs[46] = 0.0`, policy knows the pose is stale and can act cautiously

Alternative considered: terminal-transition exclusion (mask FAIL_CLOSED transitions from policy updates) — this is a **separate** training-mode decision (see P7) and can be combined with last_accepted obs.

### 7.3 v3 §6.2 patch

Insert after existing §6.2 block:

```text
FAIL_CLOSED regime propagation into error obs:
  obs[30:42] = recompute_error(hand_state, last_accepted_pose)
  (not hand_state,  est_seg_state_live because est_seg_state is the failure)
  The regime bit + confidence=0 notify policy.
```

---

## 8. P7 — FAIL_CLOSED training vs eval separation (§5.6 + §9.2 patch)

v3 conflates terminal handling across training and evaluation. v3.1 separates.

### 8.1 Evaluation mode

```text
On FAIL_CLOSED:
  - episode terminates
  - counted SEPARATELY as estimator_failure in eval metrics (not task_failure)
  - task success rate reported: per-episode, excluding estimator_failure episodes
  - overall "system success rate" reported: including estimator_failure as failure
```

This separation lets Rs see whether policy is failing the task (policy weakness) or the estimator is failing (perception weakness).

### 8.2 Training mode (MVP-3 initial choice — v3.1 recommended)

```text
On FAIL_CLOSED at step t:
  Option A (terminate immediately):
    episode ends, PPO bootstrap with V(s_{t+1}) = 0 (via dones=True)
    counted as task failure for policy update

  Option B (mask transition):
    exclude transition (s_t, a_t, r_t, done_t) from policy loss
    episode continues OR terminates depending on stale_freshness

  Option C (RECOMMENDED for v3.1 MVP-3 initial):
    allow PREDICT_TEMPORAL for up to K frames (default K=20)
    if estimator recovers within K → continue normally
    if estimator still FAIL_CLOSED at K → terminate as estimator_failure
    transitions within PREDICT_TEMPORAL included in policy update (policy learns to cope)
    transitions at FAIL_CLOSED terminal step masked from policy loss (avoid biasing value)
```

Option C rationale: gives policy time to compensate via temporal prediction while avoiding permanent stale-obs training. The mask at FAIL_CLOSED terminal step prevents policy from learning "visual fails = done" as a task-level lesson.

### 8.3 MVP-2C gate addition (v3.1)

v3 §7.1 MVP-2C exit gate adds:

```text
Additional (v3.1):
  - FAIL_CLOSED → dones=True, timeouts=False integration test PASSES (v3 retained)
  - FAIL_CLOSED training-mode behavior matches chosen Option (A / B / C, default C)
  - estimator_failure rate measured in offline eval < 10% on AC normal scenarios
    (higher failure rate indicates estimator is not ready for MVP-3 integration)
```

---

## 9. P8 — Confidence evaluation expanded (§9.1 + §7.1 MVP-2C patch)

v3 gates MVP-2C at "rank correlation > 0.7". v3.1 adds failure-detection metrics.

### 9.1 Additional MVP-2C gates (v3.1)

```text
Failure detection AUROC:
  label: residual > task threshold (cable: 5mm, clip: 3mm)
  score: 1 - confidence
  gate: AUROC > 0.85

High-confidence bad estimate rate:
  subset: confidence > 0.8
  gate: P(residual > 5mm | confidence > 0.8) < 2%

Calibration:
  bucket confidence into 10 equal-frequency bins
  compute Expected Calibration Error (ECE)
  report reliability diagram
  gate: ECE < 0.1 (loose calibration acceptable for MVP-2C; tightening deferred to MVP-3+)
```

### 9.2 Rationale

"High-confidence bad estimate rate" is the most policy-destructive failure mode: policy trusts obs because confidence is high, but obs is wrong. Rank correlation alone doesn't capture this — residuals could rank-correlate with confidence while the tail (high-conf / high-residual) is fat.

---

## 10. P9 + P10 — Stage 2 binary threshold selection + normalized point count gate (§5.3 patch)

### 10.1 Binary threshold selection (P9, §5.3 patch)

v3 §5.3: "binary weights (threshold > 0.5)". v3.1 replaces:

```text
Stage 3 residual uses binary masks only (v3 retained).
Threshold is SELECTED on validation set and then FROZEN per model version.
Default search grid: {0.3, 0.4, 0.5, 0.6, 0.7}
Selection criterion:
  maximize high-confidence valid point recall
  subject to false-positive rate on gripper/body < 5%
Record selected threshold in estimator model metadata (not in code constant).
```

### 10.2 Normalized visible_point_ratio gate (P10, §5.3 patch)

v3 §7.1 MVP-1 gate: "cable > 200 valid weighted points". v3.1 replaces with disjunction:

```text
MVP-1 gate (v3.1):
  cable: valid_points > 200 OR visible_point_ratio > 0.6
  clip : valid_points > 50  OR visible_point_ratio > 0.5

where:
  visible_point_ratio = valid_points / expected_visible_points_from_ROI
  (expected count computed from ROI area × expected density per ROI stratum)
  mask_depth_agreement = valid_depth_pixels / mask_pixels
  (auxiliary metric, > 0.8 target)
```

Rationale: wrist camera viewpoints vary widely with manipulation phase. Absolute count alone undercounts close-up / small-ROI frames (where 100 points might be sufficient) and overcounts distant / large-ROI frames (where 200 points might still miss).

---

## 11. P11 — Passive cross-skill replay (§7.1 MVP-0B+ patch)

v3 scopes to AC-only for MVP-0A~3. This is correct for integration. v3.1 adds **passive replay** for AR / Grip / IC:

### 11.1 MVP-0B+ passive replay (v3.1 addition)

```text
MVP-0B+ (v3.1 scope addition, subset of MVP-0B):
  Scope:
    - AC env integration only (same as v3)
    - PASSIVE wrist RGB-D replay collected from AR, Grip, IC scene runs
    - no env obs replacement for non-AC scenes
    - no policy integration for non-AC scenes
    - ONLY segmentation + point-cloud visibility report on collected replay

  Exit criteria:
    - AC mIoU remains within MVP-0B gates (primary)
    - AR / Grip / IC mIoU measured and reported (no hard gate — observational)
    - failure modes specific to AR / Grip / IC identified early
    - if AR / Grip / IC mIoU < 0.5 on any stratum: flag for MVP-4 design refinement

  Rationale: detect "AC works but Grip is fully occluded" problems before MVP-4.
```

This keeps MVP-3 scope AC-only while surfacing cross-skill visual failure modes early.

---

## 12. P12 — Warm-start strategy priority reorder (§5.4 + §7.1 MVP-2A patch)

v3 §5.4 lists DD-PINN first in solver flow, with PCA as fallback. v3.1 reverses priority to reflect actual implementation risk.

### 12.1 v3 §5.4 "Recommended solver structure" patch

Replace v3's flow with:

```text
point_cloud (binary weighted) + priors
        |
        v
Warm-start (priority order, v3.1):
  1. previous frame estimator state (always available after frame 0)
  2. analytic PCA / spline centerline warm start (no training cost, R6-pure)
  3. DD-PINN surrogate (CANDIDATE ONLY, used only if 1+2 fail latency / convergence basin gate)
        |
        v
Hard idempotent projection P (on 40-seg Cosserat manifold)
        |
        v
Robust local refinement (Levenberg-Marquardt, max 10 iters, Warp kernel)
        |
        v
Final 40-seg state + per-seg residual + global residual + fit confidence (physical)
```

### 12.2 v3 §7.1 MVP-2A patch

Replace MVP-2A description:

```text
MVP-2A (v3.1): Warm-start strategy comparison
  Evaluate three warm-start candidates in parallel:
    (1) previous-frame state alone
    (2) analytic PCA / spline centerline
    (3) DD-PINN candidate (requires pre-existing dataset, gated on dataset-cost feasibility)

  Exit criteria:
    - at least ONE candidate produces proposals within projection convergence basin
      for > 90% of frames (basin: 10 LM iters reduce residual >= 90%)
    - preferred: (1) or (2) sufficient (R6-pure, no training cost)
    - (3) DD-PINN adopted only if (1)+(2) fail latency or convergence gate
```

### 12.3 Rationale

v3 already acknowledges DD-PINN domain mismatch (CC3-3) and provides PCA fallback. v3.1 makes the fallback the **primary** candidate to reduce over-commitment to DD-PINN before dataset cost is known.

---

## 13. Revised OQ list (v3.1)

Replacing v3 §11:

```text
OQ-1a: Concept approval  (v3.1 new, see §2)
  Approve Option C-2R direction and MVP-0A scoping work (offline replay, no cuda:0).

OQ-1b: Implementation gate  (v3.1 new, see §2)
  Approve MVP-0A full impl + subsequent MVPs after Stage 1 measured benchmark passes.

OQ-2: MVP scope  (v3 retained)
  AC-only MVP-0A → MVP-3; MVP-4 deferred pending OQ-5.

OQ-3: Implementation timing  (v3 retained)
  Offline replay default; parked until Phase 5-1 priorities clear.

OQ-4: DR noise distribution  (v3 retained)
  Placeholder σ_pos=3mm / σ_ori=0.03 rad; measurement-driven at MVP-2B.

OQ-5: per-skill obs SSOT consolidation  (v3 retained, MVP-4 blocker)
  (A) unify to 42D / (B) per-skill heads / (C) defer IC.

OQ-6: Sim-to-real PoC timing  (v3 retained)
  Defer until MVP-4 or un-park.
```

Total: 7 OQs (v3.1).

---

## 14. v3.1 revision history

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| v1 | 2026-04-25 06:00 | CC#4 | Initial proposal, 620 lines, superseded by v2 |
| v2 | 2026-04-25 06:55 | Rs (improved from v1) | Execution-oriented restructure, 1061 lines, stock per Rs X2 |
| v3 | 2026-04-25 07:10 | CC#4 (post-debate) | 5-CC Debate revision, 5 CRIT + 14 HIGH resolved + IC 45D env finding, 1416 lines |
| **v3.1** | **2026-04-25 07:30** | **CC#4 (Rs 12-point feedback patch)** | **5 essential + 7 supporting improvements**, patch document form |

---

## Appendix D: Estimator Input Boundary (new in v3.1)

### D.1 Principle

The estimator must produce physically-meaningful object pose **from robot-accessible signals only**. GT object state is for **offline evaluation only**, never flows into estimator inference.

Violation of this boundary breaks:
- R6 observation grounding (NN learning from oracle, not sensors)
- sim-to-real transfer feasibility
- MVP-2/3 residual reporting validity
- entire value proposition of pose estimation design

### D.2 Allowed inputs (whitelist)

| Input | Source | Notes |
| --- | --- | --- |
| Wrist RGB image | `WristCameraManager.color_tensor` | Primary sensor |
| Wrist depth image | `WristCameraManager.depth_tensor` | Primary sensor |
| Camera intrinsics | static (FOV=45°, 128², pixel scale 0.86 mm/px at 133 mm) | `task_config.py` |
| Camera extrinsics | derived from wrist body_q + LOCAL_POS offset | `wrist_camera_manager.py:129-148` computation |
| Arm joint position | `state.joint_q` (Newton) or proprio in real | Robot-available |
| Arm joint velocity | `state.joint_qd` or proprio finite-difference | Robot-available |
| Wrist camera body pose | body_q[wrist_L] = body 6, body_q[wrist_R] = body 15 | **Allowed, this is robot kinematics, not object state** |
| Gripper / finger geometry | static mesh vertices in world frame (computed from body_q[finger bodies]) | For self-occlusion projection |
| Routing target seg index | orchestrator-provided | Routing state (integer), not GT pose |
| Routing target clip index | orchestrator-provided | Routing state (integer) |
| Previous estimator state | `PoseEstimate14D` from previous frame | Self-referenced, not GT |

**Rule:** if a wrist-robot system can measure it physically, it is allowed. Joint encoders, force/torque, cameras, proprio all qualify.

### D.3 Forbidden inputs (blacklist)

| Forbidden | Why | Violation consequence |
| --- | --- | --- |
| `state.body_q[cable_body_idx]` | this IS the GT we are replacing | R6 hard violation; estimator becomes oracle passthrough |
| `state.body_q[clip_body_idx]` under DR | nominal is wrong under DR | R6 soft violation (nominal lie) |
| `state.body_q[target_seg_idx]` | GT pose of output target | R6 hard violation |
| Any Newton `state` except for **eval labels** | sim-state bypass | breaks sim-to-real and R6 |
| Future-frame state | oracle look-ahead | unrealistic in real deployment |
| Reward components or success signals | cross-contamination | reward hacking surface |

### D.4 API type separation

```python
from dataclasses import dataclass
import torch
import inspect
import re


@dataclass
class EstimatorInputs:
    """MUST contain only allowed inputs (§D.2).

    Any tensor here is robot-measurable in simulation and real.
    """
    rgb_l: torch.Tensor
    rgb_r: torch.Tensor
    depth_l: torch.Tensor
    depth_r: torch.Tensor
    joint_state: torch.Tensor
    wrist_camera_pose_l: torch.Tensor
    wrist_camera_pose_r: torch.Tensor
    gripper_geometry_l: torch.Tensor
    gripper_geometry_r: torch.Tensor
    routing_target_seg_idx: torch.Tensor
    routing_target_clip_idx: torch.Tensor
    previous_estimate: "PoseEstimate14D | None"


@dataclass
class EstimatorLabelsForEvalOnly:
    """GT labels for OFFLINE EVALUATION ONLY.

    Never passes through PoseEstimatorV1.forward.
    Only EvalPoseEstimator.compare may access both estimate and these labels.
    """
    gt_cable_body_q: torch.Tensor    # [B, 40, 7]
    gt_clip_pose: torch.Tensor       # [B, 5, 7]
    gt_target_seg_idx: torch.Tensor  # [B]


def enforce_input_boundary(fn):
    """Decorator: reject any parameter that looks like GT or sim state."""
    forbidden_substrings = ('body_q', 'gt_', 'ground_truth', 'state_0')
    sig = inspect.signature(fn)
    for pname in sig.parameters:
        if any(sub in pname.lower() for sub in forbidden_substrings):
            raise TypeError(
                f"{fn.__name__} cannot accept GT-like parameter '{pname}'. "
                f"Allowed inputs defined in Appendix D.2."
            )
    return fn


class PoseEstimatorV1:
    @enforce_input_boundary
    def forward(self, inputs: EstimatorInputs) -> "PoseEstimate14D":
        """Estimator inference; GT must not appear in signature."""
        ...
```

### D.5 Mandatory integration tests (v3.1 required for MVP-0A merge)

```python
def test_estimator_input_boundary_typing():
    """Compile-time check that EstimatorInputs contains no GT fields."""
    gt_fields = {'gt_cable_body_q', 'gt_clip_pose', 'gt_target_seg_idx', 'body_q'}
    estimator_inputs_fields = set(EstimatorInputs.__dataclass_fields__.keys())
    assert estimator_inputs_fields.isdisjoint(gt_fields), \
        "EstimatorInputs must not contain GT fields"


def test_no_gt_in_estimator_module():
    """Grep module source for forbidden patterns."""
    import pathlib
    estimator_dir = pathlib.Path('thread_isaac_lab/estimators/')
    forbidden = [
        r'\.body_q\[.*cable',
        r'\.body_q\[.*target',
        r'GROOVE_TARGET',
        r'self\._state\.body_q',
    ]
    for src in estimator_dir.rglob('*.py'):
        text = src.read_text()
        for pat in forbidden:
            assert not re.search(pat, text), \
                f"{src}: forbidden pattern '{pat}' detected"


def test_eval_label_only_in_eval():
    """Labels appear only in eval code, not in estimator inference."""
    import pathlib
    estimator_inference = pathlib.Path('thread_isaac_lab/estimators/pose_estimator_v1.py').read_text()
    assert 'EstimatorLabelsForEvalOnly' not in estimator_inference, \
        "Eval labels leaked into inference module"
```

---

## Appendix E: Policy Migration Plan 42D → 47D (new in v3.1)

### E.1 Scope

AC skill only (MVP-3 integration target per v3 §6.1 AC-only scoping). AR / Grip / IC deferred per OQ-5.

### E.2 Starting state

- Baseline: converged AC policy trained on GT obs 42D (per `RL-Routing-Progress.md`)
- Checkpoint: end-of-training baseline (not mid-training)
- Architecture: PPO with MLP actor + critic, obs dim 42 → actions 12 + value scalar

### E.3 Obs normalizer migration

THREAD uses RSL-RL running observation normalizer (mean / std per dim).

```python
def migrate_obs_normalizer_42_to_47(old_normalizer_42):
    """Extend 42D running stats to 47D for AC augmented obs."""
    new_normalizer_47 = RunningObservationNormalizer(dim=47)

    # Inherit old 42D running stats
    new_normalizer_47.mean[:42] = old_normalizer_42.mean
    new_normalizer_47.var[:42] = old_normalizer_42.var
    new_normalizer_47.count = old_normalizer_42.count

    # Initialize new 5D (ACCEPT one-hot + confidence)
    # ACCEPT = [1, 0, 0, 0]
    new_normalizer_47.mean[42:46] = torch.tensor([1.0, 0.0, 0.0, 0.0])
    new_normalizer_47.var[42:46] = 0.01 ** 2  # epsilon var

    # Confidence = 1.0 at initial training (all ACCEPT with high conf)
    new_normalizer_47.mean[46] = 1.0
    new_normalizer_47.var[46] = 0.01 ** 2

    return new_normalizer_47
```

### E.4 Network first-layer weight migration

Most policy architectures use a first-layer Linear(obs_dim, hidden_dim). Expand from 42 → 47 by weight extension:

```python
def migrate_first_layer_42_to_47(old_first_layer: torch.nn.Linear):
    """Expand first-layer input dim from 42 to 47 with zero-init for new dims."""
    assert old_first_layer.in_features == 42
    hidden_dim = old_first_layer.out_features
    new_first_layer = torch.nn.Linear(47, hidden_dim)

    # Copy old 42D weights
    new_first_layer.weight.data[:, :42] = old_first_layer.weight.data

    # Zero-init new 5D weights
    new_first_layer.weight.data[:, 42:47] = 0.0

    # Bias unchanged
    new_first_layer.bias.data = old_first_layer.bias.data.clone()

    return new_first_layer


def migrate_policy_42_to_47(baseline_ckpt_path, new_ckpt_path):
    """Full policy migration."""
    sd = torch.load(baseline_ckpt_path)

    # Identify first layer name (depends on architecture)
    first_layer_key = 'actor.0.weight'  # example for MLP Actor(0)=Linear(42, hidden)
    old_first_weight = sd[first_layer_key]

    new_first_weight = torch.zeros(old_first_weight.size(0), 47)
    new_first_weight[:, :42] = old_first_weight
    # new_first_weight[:, 42:47] = 0  (implicit)

    sd[first_layer_key] = new_first_weight

    # Similarly for critic if it takes obs
    critic_key = 'critic.0.weight'
    old_critic = sd[critic_key]
    new_critic = torch.zeros(old_critic.size(0), 47)
    new_critic[:, :42] = old_critic
    sd[critic_key] = new_critic

    torch.save(sd, new_ckpt_path)
```

### E.5 Initial behavior guarantee

At step 0 after migration, with obs = [42D_existing, one_hot_ACCEPT=1000, confidence=1.0]:

- first_layer(obs)[:, :42] = old_layer[:, :42] @ existing_42D (same as baseline)
- first_layer(obs)[:, 42:47] = 0 @ [1,0,0,0,1] = 0 (zero contribution)

Therefore activations are bit-identical to pre-migration baseline when input new-5D is [1,0,0,0,1] (ACCEPT with conf=1). Policy output and value output are preserved.

As training proceeds, gradients flow through new 5D weights → policy learns to use regime + confidence.

### E.6 Rollback criterion

```text
Monitor during MVP-3 fine-tune:
  value_loss moving average over 20 iters

If value_loss > 3 × baseline_end_value_loss at iter 20:
  abort fine-tune
  rollback to baseline checkpoint
  fresh-start with migration re-applied
  investigate: likely DR distribution mismatch or estimator residual too high
```

### E.7 Action scale / reset noise — unchanged

This migration does NOT modify action scale, reset noise, reward, env dynamics. Only obs dim + first-layer extension + normalizer dim.

---

## Appendix F: Dataset Split Protocol (new in v3.1)

### F.1 Principle

Supervised Stage 1 training on simulated labels must NOT leak train-domain features into test evaluation. THREAD sim episodes produce many correlated frames per episode (W=32 worlds × ~500 steps = 16000 frames per episode rollout, all with identical DR seed).

### F.2 Split unit

**Split by `(episode_seed, world_index)` tuple**, NOT by frame index.

```python
def split_dataset(episodes: list[EpisodeRollout], train_frac=0.7, val_frac=0.15) -> dict:
    """
    Episodes are identified by (seed, world_index) — same seed + world = same trajectory.
    Train/val/test split uses SEED, not frame.
    """
    seeds = sorted(set(ep.seed for ep in episodes))
    rng = random.Random(42)
    rng.shuffle(seeds)

    n_train = int(len(seeds) * train_frac)
    n_val = int(len(seeds) * val_frac)

    train_seeds = set(seeds[:n_train])
    val_seeds = set(seeds[n_train:n_train + n_val])
    test_seeds = set(seeds[n_train + n_val:])

    return {
        'train': [ep for ep in episodes if ep.seed in train_seeds],
        'val'  : [ep for ep in episodes if ep.seed in val_seeds],
        'test' : [ep for ep in episodes if ep.seed in test_seeds],
    }
```

### F.3 Held-out randomization in test set

Test set MUST contain at least one stratum where a domain factor is OOD vs train:

| Factor | Train distribution | Test held-out distribution |
| --- | --- | --- |
| Lighting direction | 0-360° uniform | 4 fixed angles NOT seen in train |
| Cable color/texture | train-set cable materials | NEW texture materials |
| Camera noise σ | 0-0.02 | 0.03 (higher than train max) |
| Clip DR perturbation | trained σ | σ × 1.5 (wider) |

This ensures test mIoU reflects genuine generalization, not memorization of DR seeds.

### F.4 Occlusion strata

Each frame is labeled with occlusion stratum:

| Stratum | Criterion | Target frequency in test |
| --- | --- | --- |
| normal | no occlusion, target visible > 80% | 30% |
| partial | target visible 40-80% | 25% |
| heavy gripper | target visible < 40% due to gripper/finger | 20% |
| low mask area | object < 2% of frame pixels | 10% |
| high background clutter | table texture rich, many false-positive candidates | 15% |

Stratum labels are sourced from simulator ground truth (visibility rendering).

### F.5 Per-stratum reporting

MVP-0A / MVP-0B evaluation report format:

```text
Stage 1 Segmentation Report (MVP-0A, model v1.3, threshold=0.45)

Aggregate:
  cable mIoU: 0.83
  clip mIoU: 0.78
  ROI recall: 0.96

Per-stratum:
  normal           : cable mIoU 0.89 | clip mIoU 0.85 | ROI recall 0.98 | n_frames 3012
  partial          : cable mIoU 0.78 | clip mIoU 0.72 | ROI recall 0.95 | n_frames 2510
  heavy gripper    : cable mIoU 0.69 | clip mIoU 0.63 | ROI recall 0.88 | n_frames 2008
  low mask area    : cable mIoU 0.64 | clip mIoU 0.58 | ROI recall 0.82 | n_frames 1004
  high bg clutter  : cable mIoU 0.76 | clip mIoU 0.71 | ROI recall 0.92 | n_frames 1506

Failure subset (mIoU < 0.5):
  n_frames 312 (3.1% of test)
  dominant failure: heavy gripper + low mask area overlap (235 / 312)
```

### F.6 MVP-0A gate (v3.1 update to v3 §7.1)

```text
MVP-0A exit gate (v3.1):

Aggregate gates (v3 retained):
  cable mIoU > 0.8
  clip mIoU > 0.75
  ROI recall > 0.95

Per-stratum gates (v3.1 addition):
  normal           : cable > 0.85, clip > 0.80
  partial          : cable > 0.75, clip > 0.70
  heavy gripper    : cable > 0.65, clip > 0.60
  low mask area    : cable > 0.60, clip > 0.55
  high bg clutter  : cable > 0.75, clip > 0.70

Auxiliary (v3 retained):
  depth-valid head AUROC > 0.85 on val set
  occlusion head AUROC > 0.80 on val set
```

MVP-0A passes only if ALL gates pass on the test set (held-out seeds).

---

## Appendix G: Numerical Test Tolerances (new in v3.1)

### G.1 Test categories

The estimator has multiple numerical contracts. Tolerances differ by test purpose.

| Category | Purpose | Platform | Tolerance |
| --- | --- | --- | --- |
| Mathematical correctness | verify algorithm / operator is sound | CPU fp64 with fixed seed | very tight (1e-10 to 1e-8) |
| Implementation fidelity | verify production code preserves the contract | GPU fp32 or mixed fp16 | realistic (1e-5 to 1e-4) |
| Invariant preservation | property-based | either | category-specific |
| Regression stability | detect drift over commits | prod platform | loose enough for CI noise |

### G.2 Projection idempotency (P(P(x)) = P(x))

```text
CPU fp64 deterministic (REQUIRED for MVP-2B):
  fixed seed 42
  input q0 sampled uniformly
  tolerance:
    position max absolute: 1e-10 m
    quaternion angular (geodesic): 1e-10 rad
  failure: assertion raised with diff

GPU fp32 production (REQUIRED for MVP-2B):
  cuda:0 or cuda:2, batch=32
  tolerance:
    ||P(P(q0))_pos - P(q0)_pos||_inf < 1e-5 m (0.01 mm)
    max quaternion angular: 1e-5 rad
    constraint_residual(P(q0)) <= constraint_residual(q0) * 1.01 (non-increasing)
  failure: warn with stats, block merge

GPU fp16 mixed (MVP-3 optional):
  tolerance same as fp32 but relaxed by 10x
    pos: 1e-4 m (0.1 mm)
    ang: 1e-4 rad
```

### G.3 Quaternion convention match (CC4-6 v3 §9.1)

```text
CPU fp64 (REQUIRED):
  draw 100 random SO(3) rotations
  compute PoseEstimate14D.seg_quat_w from synthetic body_q
  compare byte-equal to Newton body_q[seg_idx, 3:7] convention
    (xyzw, w>=0 canonicalized)
  tolerance: exact bit-equality after w>=0 flip

GPU fp32 (REQUIRED):
  as above but batch tensor
  tolerance: max element-wise diff < 1e-6 (fp32 single bit LSB)
```

### G.4 Per-world isolation (CC4-4 v3 §9.1)

```text
Platform: either (test is integer indexing, not floating)
  reset world 3, ensure worlds {0, 1, 2, 4, 5, ...} tensors bit-equal before and after
  tolerance: bit-exact on integer tensors, 0 on fp tensors
```

### G.5 R6 hard test: zero-visible-points → prior-only

```text
CPU fp64 (REQUIRED for MVP-2B exit):
  input: zero point cloud (N=0)
  input: prior state q_prior
  input: DD-PINN-shaped arbitrary warm-start q_surrogate != q_prior
  expect: output == P(q_prior) within 1e-8
  MUST NOT be q_surrogate-shaped

GPU fp32 (REQUIRED):
  as above
  tolerance: pos < 1e-5 m, ang < 1e-5 rad vs P(q_prior)
```

### G.6 Cable pose accuracy (MVP-2B gate)

```text
Platform: GPU fp32 (production)
  subject to measured residual, NOT the numerical idempotency test
  gates (v3 §9.1 unchanged):
    cable target pos error < 5 mm
    cable target ori error < 0.05 rad
  measured on test-set held-out episodes
```

### G.7 Summary table

| Test | Priority | CPU fp64 tol | GPU fp32 tol | GPU fp16 tol |
| --- | --- | --- | --- | --- |
| Projection idempotent | MVP-2B | 1e-10 | 1e-5 m / 1e-5 rad | 1e-4 |
| Quat convention | MVP-2B | bit-equal | 1e-6 | — |
| Per-world isolation | MVP-0A+ | bit-equal | bit-equal | — |
| R6 zero-vis | MVP-2B | 1e-8 | 1e-5 | — |
| Cable pose accuracy | MVP-2B | — | 5 mm / 0.05 rad | — |

---

## 15. Env obs shape verification (v3.1 addendum, post-review env verification)

### 15.1 Finding: all 4 envs emit 45D unified (not 42D)

v3 §1.1 stated "AC/AR/Grip follow RL-Routing-Design 42D (common)". Direct env verification (2026-04-25 07:45) shows a more accurate picture:

| Env | Mode | Emitted tensor shape | Pose block location | Notes |
| --- | --- | --- | --- | --- |
| AC | default | **45D** (42D + 3D zero pad at `[42:45]`) + optional visual_feat | `obs[16:30]` | `newton_approach_cable_env.py:1324-1345` |
| AR | default | **45D** (42D + 3D zero pad at `[42:45]`) | `obs[16:30]` | `newton_aerial_regrasp_env.py:748-752` |
| Grip | `_dual_arm=True` | **45D** (42D + 3D zero pad at `[42:45]`) | `obs[16:30]` | `newton_grip_env.py:1012-1082` |
| Grip | `_dual_arm=False` | **28D per-arm** (N × 2 slots, not per-world) | `obs[8:22]` (different!) | `newton_grip_env.py:922-1008` |
| IC | default | **45D** (groove-relative, native) | `obs[14:20]` axis-angle error | `newton_insert_clip_env.py:1165-1181` |

Key observations:
- **No env emits 42D directly**. AC / AR / Grip-dual pad to 45D for IC-compatible unified base model input.
- IC is the shape-anchor (45D native); other envs pad to match.
- The pad at `[42:45]` is constant zero — structural, not policy state.
- **Grip single-arm mode** (`_dual_arm=False`) emits `[2N, 28]` per-arm tensor — fundamentally different structure. v3 / v3.1 do not cover this mode; pose estimation integration for Grip single-arm is out of scope until single-arm mode status is clarified.

### 15.2 Impact on v3.1 47D augmented obs (Appendix E update)

v3.1 §6.4 / Appendix E assumed `augmented_obs = 42D + 5D = 47D`. Env reality shows base model input is **45D unified**, not 42D. Therefore augmented obs should be:

```text
augmented_obs (AC/AR/Grip-dual) = 45D unified + 5D (4D state + 1D conf) = 50D
    layout: [0:16] proprio | [16:30] pose block | [30:42] error | [42:45] zero pad | [45:49] state one-hot | [49] conf

augmented_obs (IC) = 45D groove-relative + 5D = 50D (same shape but different semantics at [0:45])
    deferred per OQ-5

Grip single-arm (_dual_arm=False): 28D per-arm + 5D = 33D per-arm
    deferred (not targeted in MVP-0A~3)
```

### 15.3 Appendix E revision (42D→50D instead of 42D→47D)

Replace Appendix E §E.4 (first-layer migration) with:

```python
def migrate_policy_45_to_50(baseline_ckpt_path, new_ckpt_path):
    """Full policy migration 45D → 50D (v3.1 addendum correction).

    Base model previously takes 45D obs (unified across AC/AR/Grip-dual/IC).
    Augment with 4D regime one-hot + 1D confidence = 50D.
    """
    sd = torch.load(baseline_ckpt_path)

    for first_layer_key in ('actor.0.weight', 'critic.0.weight'):
        old_weight = sd[first_layer_key]
        assert old_weight.size(1) == 45, f"Expected 45D input, got {old_weight.size(1)}"
        hidden_dim = old_weight.size(0)
        new_weight = torch.zeros(hidden_dim, 50)
        new_weight[:, :45] = old_weight           # copy existing
        new_weight[:, 45:50] = 0.0                # zero-init new 5D
        sd[first_layer_key] = new_weight

    torch.save(sd, new_ckpt_path)
```

Initial behavior guarantee: at training step 0, with new 5D = `[1, 0, 0, 0, 1.0]` (ACCEPT regime + conf=1.0), first-layer activations are bit-identical to 45D baseline (since zero-init contribution is 0).

### 15.4 OQ-5 scope refinement (v3.1 addendum)

v3 §2.5 identified IC's 45D divergence as SSOT consolidation blocker. v3.1 env verification refines the picture:

| Skill | Emitted shape | Pose semantic | SSOT consolidation needed? |
| --- | --- | --- | --- |
| AC | 45D (padded) | absolute pose at [16:30] | **No — pose block matches RL-Routing-Design §4** |
| AR | 45D (padded) | absolute pose at [16:30] | **No — same as AC** |
| Grip dual-arm | 45D (padded) | absolute pose at [16:30] | **No — same as AC** |
| Grip single-arm | 28D per-arm | absolute pose at [8:22] | **Yes — structurally different, MVP-0A~3 excludes this mode** |
| IC | 45D (native) | groove-relative error at [14:20] | **Yes — fundamentally different semantics** |

**Refined OQ-5 (v3.1 version):**

```text
OQ-5a: Confirm Grip dual-arm mode as MVP-0A~3 target (Grip single-arm excluded)
OQ-5b: Decide IC strategy — (A) unify IC to 45D absolute-pose / (B) per-skill heads / (C) defer IC entirely
OQ-5c: Document unified 45D base model input contract in RL-Routing-Design.md §4
       (current §4 table is 42D; env reality is 45D)
```

### 15.5 v3 §1.1 per-skill table correction

Replace v3 §1.1 AC/AR/Grip table row headers:

```text
Was (v3): "AC / AR / Grip (42D common)"
Now (v3.1 addendum): "AC / AR / Grip-dual (45D unified, 42D content + 3D zero pad)"

Was (v3 §6.1): "AC policy obs at MVP-3: 47D"
Now (v3.1 addendum): "AC policy obs at MVP-3: 50D (45D unified + 4D state + 1D conf)"
```

### 15.6 Why this matters for v3.1

- Appendix E zero-init adapter math: correct form uses 45D→50D, not 42D→47D
- Gridding of MVP-3 expected regressions: obs distribution analysis must use 45D stats, not 42D
- Obs normalizer migration preserves 45 dims, initializes 5 new dims
- Rollback criterion and gate arithmetic unchanged (just shape re-reading)

Implementation delta from v3.1 original form: 3 digit changes (42→45, 47→50) plus acknowledgement that padding `[42:45]=0` is structural. No algorithm change; no design direction change.

---

## Summary (v3.1)

v3.1 retains v3's design direction (C-2R, AC-only, MVP-4 deferred, augmented regime-visible obs, hard projection, fallback-to-policy visible). v3.1 adds 12 targeted improvements (5 Rs-essential + 7 supporting) as patches to v3. Plus post-review §15 env verification correcting obs shape 42D→45D and 47D→50D arithmetic. Net impact:

- **OQ-1a / OQ-1b split** unblocks benchmark production
- **Estimator Input Boundary (Appendix D)** prevents the most catastrophic failure mode (GT leaking into estimator inference) with type + test enforcement
- **Policy migration (Appendix E)** minimizes MVP-3 checkpoint collapse risk via zero-init adapter
- **Projection tolerance (Appendix G)** allows realistic GPU implementation without losing R6 hard test
- **Dataset split (Appendix F)** prevents train/test leak and hidden occlusion failures
- 7 supporting patches address FAIL_CLOSED semantics, confidence evaluation, binary threshold, normalized point count, training/eval separation, passive cross-skill replay, warm-start priority

v3.1 is intentionally a **patch** (~900 lines) not a full rewrite — reader opens v3 + v3.1 together. Rs directive honored: "設計をさらに長くするより、5点だけを v3.1 patch として足す".

Next action: Rs approval on OQ-1a (concept + benchmark permit) + OQ-5 (SSOT consolidation). OQ-1b and later remain gated until benchmark results.
