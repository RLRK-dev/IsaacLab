---
status_ledger: 00-DESIGN-STATUS-LEDGER.md  # authoritative success/failure status SSOT
title: Pose Estimation Design v2 — obs[16:29] Replacement via Wrist RGB-D + Joint State
created: "2026-04-25T06:00:00+09:00"
updated: "2026-04-25T06:55:00+09:00"
status: "Proposal / Parked Design Stock — implementation gated by Rs decision"
owner: "CC#4 / Pose Estimation Research"
tags:
  - design
  - vision
  - pose-estimation
  - cable
  - clip
  - msa-42d
  - sim-to-real-prep
  - parked-vision-stack
---

# Pose Estimation Design v2

> **⚠ WHOLE-SUPERSEDED (archive) — renewal batch B, 2026-07-11 (banner-only; content edit-frozen):** this document is **superseded in whole** by v3 (`00-DESIGN-STATUS-LEDGER.md:53` = 🔁 **SUPERSEDED** → v3). It is **not** part of the current head stock (head = v3.2 over v3.1 over v3). Retained as historical record only. Current head: `[[PoseEstimation-Design-v3.2]]` (`:50`, PARKED/unvalidated). Status SSOT = `00-DESIGN-STATUS-LEDGER.md`.

## 0. Executive decision

### Recommendation

Adopt **Option C-2R: Routing-conditioned Hybrid pose estimation** as the target design for replacing `obs[16:29]`.

The recommended stack is:

1. **Stage 0: Kinematic prior and ROI proposal**
   - Input: previous cable estimate, current joint/body state, routing target, nominal clip poses.
   - Output: camera-space ROIs, robot self-occlusion masks, prior segment distribution.
   - Purpose: constrain the visual problem before the NN runs.

2. **Stage 1: Light segmentation + confidence model**
   - Input: wrist RGB-D, left and right wrist cameras.
   - Output: cable mask, five clip instance masks, depth-validity mask, occlusion likelihood, per-object confidence.
   - Candidate: light U-Net or Fast-SCNN-style encoder first; SAM2 fine-tuning remains a later, heavier variant.

3. **Stage 2: Analytic 3D reconstruction**
   - Input: masks, depth, camera intrinsics, camera-to-world transforms from joint/body state.
   - Output: cable and clip point clouds in world frame, with per-point confidence weights.

4. **Stage 3: Surrogate-assisted constrained refinement**
   - Cable: DD-PINN or lightweight rod surrogate proposes a warm start; a constrained projection step enforces segment length, continuity, temporal consistency, and routing-local constraints.
   - Clip: CAD-based rigid pose refinement per clip.
   - Output: full cable segment poses and five clip poses.

5. **Stage 4: Probabilistic temporal filter and fallback gate**
   - Input: previous estimate, current estimate, routing target, MSA phase.
   - Output: stable 13D replacement for `obs[16:29]`, confidence, covariance proxy, and explicit ACCEPT / PREDICT / FALLBACK state.

### Implementation stance

This design should remain **parked** until Vision Stack un-park or sim-to-real preparation is explicitly prioritized.

Immediate implementation is **not required** for the current sim-only Phase 5 path because the existing ground-truth observation route is sufficient for simulator training. The value of this document is to provide a ready-to-execute design once `obs[16:29]` must become physically observable.

### MVP recommendation

Start with **MVP-0A and MVP-0B** when implementation is approved:

| MVP | Scope | Exit gate |
| --- | --- | --- |
| MVP-0A | Stage 0 + Stage 1 segmentation, one wrist camera, AC environment only, no env mutation | Cable and clip masks are visually stable; target mIoU exceeds 0.8 on generated sim labels |
| MVP-0B | Add second wrist camera and ROI/self-occlusion masking | Two-view fusion improves target visibility and reduces false positives under grip-like occlusion |

Do not begin with full obs replacement. The first objective is to prove whether wrist RGB-D can produce sufficiently clean masks under the exact THREAD camera geometry and occlusion regime.

---

## 1. Design goal

### 1.1 Problem statement

The current MSA observation vector is 42D. Within it, `obs[16:29]` is a 13D block containing target cable segment pose and target clip pose:

| Slice | Meaning | Dim | Current source |
| --- | --- | ---: | --- |
| `obs[16:19]` | target cable segment position, XYZ | 3 | Newton `state.body_q[target_seg_idx][:3]` |
| `obs[19:23]` | target cable segment orientation, quaternion `xyzw`, canonicalized with `w > 0` | 4 | Newton `state.body_q[target_seg_idx][3:7]` |
| `obs[23:26]` | current target clip position, XYZ | 3 | routing index + `task_config.py` clip constants |
| `obs[26:30]` | current target clip orientation, quaternion | 4 | routing index + fixed clip quaternion |

The design mission is to replace this simulator-only 13D ground-truth block with an estimate derived from:

- on-hand wrist RGB-D cameras,
- arm joint / body state,
- known cable and clip geometry,
- routing state.

### 1.2 Why this matters

The existing observation path blocks future sim-to-real transfer because real hardware cannot read Newton `body_q` for cable or clip poses. Even if the current policy works in simulation, a policy trained on noiseless ground truth will face a distribution shift when deployed with vision-derived observations.

The replacement design must therefore solve two distinct problems:

1. **Observability:** make target cable and clip pose measurable from robot sensors.
2. **Policy compatibility:** preserve the 42D observation contract so current skill policies can be fine-tuned rather than fully redesigned.

### 1.3 Non-goals

This design does not authorize immediate implementation. It also does not change:

- environment reward definitions,
- success conditions,
- action space,
- MSA skill routing semantics,
- Newton VBD cable dynamics,
- wrist camera manager internals,
- training launch configuration.

The first implementation should be a sidecar estimator and evaluator, not an env-integrated policy dependency.

---

## 2. Design constraints

### 2.1 THREAD-specific constraints

| Constraint | Current value / implication |
| --- | --- |
| Physics backend | Newton VBD is primary. PhysX remains legacy because of N-dependency and cable tunneling issues at larger world counts. |
| Parallel worlds | Target design must support W=32 batched worlds. |
| Cable representation | Cable is a 40-body segmented rod; target segment is selected by routing plan, often with ±1 segment tolerance. |
| Wrist cameras | Left wrist body 6, right wrist body 15, RGB-D, 128×128, FOV 45°. |
| Pixel scale | Approx. 0.86 mm/px at 133 mm working distance. |
| Task precision | `T_DIST = 2 mm`, `T_GROOVE = 3 mm`, `EE_TO_FINGERTIP = 220 mm`. |
| Existing camera overhead | W=32, C=2, 128² RGB-D adds roughly 6% per step. |
| Policy contract | MSA uses 42D observation and 12D action across AC / IC / AR / Grip. |
| Clip geometry | Five identical clips at known nominal placements; CAD is assumed available. |

### 2.2 R6 observation-grounding constraint

The estimator must preserve the R6 principle:

- Learning may decode sensor-specific observations into intermediate percepts.
- Physical quantities used by policy must remain constrained by geometry or physics.
- A neural network must not be the sole definition of a physical pose.

This strongly disfavors a pure image-to-pose regressor for the final design.

### 2.3 Primary acceptance criteria

The estimator is viable only if it satisfies these gates:

| Gate | Target |
| --- | --- |
| Observation compatibility | Emits exactly the same 13D semantic contract as current `obs[16:29]`. |
| Position accuracy | Cable target segment position error under 5 mm for MVP-2; long-term target under 2–3 mm. |
| Orientation accuracy | Cable target segment orientation error under 0.05 rad for MVP-2. |
| Policy compatibility | AC success after estimator integration reaches at least 90% of GT-observation baseline before expanding to all skills. |
| Performance | Total estimator overhead remains within the approximate 10–12% combined rendering + estimator budget. |
| Debuggability | Each stage emits diagnostics sufficient to distinguish segmentation, depth, geometry-fit, and temporal-filter failures. |

---

## 3. Target system overview

### 3.1 Dataflow

```text
Wrist RGB-D + joint/body state + routing state
        |
        v
Stage 1: semantic / instance segmentation
        |
        v
Stage 2: masked depth back-projection to world-frame point clouds
        |
        v
Stage 3a: cable rod fitting over 40 segments
Stage 3b: clip CAD pose fitting over 5 clip instances
        |
        v
Stage 4: temporal consistency, target lookup, confidence gating
        |
        v
obs[16:29] replacement + estimator diagnostics
```

### 3.2 Output contract

The estimator must return two outputs: the observation replacement and diagnostics.

```python
@dataclass
class PoseEstimate13D:
    seg_pos_w: torch.Tensor      # [W, 3]
    seg_quat_w: torch.Tensor     # [W, 4], xyzw, canonicalized w >= 0
    clip_pos_w: torch.Tensor     # [W, 3]
    clip_quat_w: torch.Tensor    # [W, 4], xyzw, canonicalized w >= 0

    def as_obs_block(self) -> torch.Tensor:
        # [W, 13] matching obs[16:29]
        return torch.cat(
            [self.seg_pos_w, self.seg_quat_w, self.clip_pos_w, self.clip_quat_w],
            dim=-1,
        )
```

Diagnostics are not part of the 42D policy observation in the initial replacement mode:

```python
@dataclass
class PoseEstimatorDiagnostics:
    cable_mask_area: torch.Tensor        # [W]
    clip_mask_area: torch.Tensor         # [W, 5]
    cable_point_count: torch.Tensor      # [W]
    clip_point_count: torch.Tensor       # [W, 5]
    cable_fit_residual_mm: torch.Tensor  # [W]
    clip_fit_residual_mm: torch.Tensor   # [W, 5]
    seg_confidence: torch.Tensor         # [W]
    clip_confidence: torch.Tensor        # [W]
    used_prediction: torch.Tensor        # [W], bool
    failure_code: torch.Tensor           # [W], enum/int
```

### 3.3 Responsibility boundary

| Module | Responsibility | Explicitly not responsible for |
| --- | --- | --- |
| `WristCameraManager` | Provide RGB-D tensors and camera transforms | Estimator inference, policy obs mutation |
| `PoseEstimatorV1` | Convert visual/proprioceptive inputs into 13D physical pose estimates | Reward calculation, skill routing, training policy |
| `ObsAssembler` or env wrapper | Replace `obs[16:29]` and recompute dependent error obs | Camera rendering, segmentation training |
| `EvalPoseEstimator` | Compare estimator output against sim ground truth | Policy optimization |
| `TrainSegmenter` | Train / validate Stage 1 masks from sim labels | Env integration |

The first implementation should keep `WristCameraManager` unchanged and attach the estimator above `extras["visual_obs"]`.

---

## 4. Architecture choice

### 4.1 Option comparison

| Axis | Option A: Pure geometry | Option B: Pure NN | Option C: Hybrid | Option D: Differentiable rendering |
| --- | --- | --- | --- | --- |
| R6 alignment | Strong | Weak | Strong | Strong |
| 2 mm feasibility | Medium-low | Uncertain | Medium-high | High |
| Occlusion handling | Weak | Medium | Medium-high | Medium |
| Sim-to-real risk | Low-medium | High | Low-medium | Low-medium |
| W=32 feasibility | Medium | High | Medium-high | Low-medium |
| Debuggability | High | Low | High | Medium |
| Implementation risk | Medium | Medium | Medium | High |
| Recommended role | Baseline / ablation | Rejected for final pose | Primary design | Long-term refinement tool |

### 4.2 Why Option C is the right default

Option C is the best fit because it isolates learning to the least dangerous part of the pipeline: segmentation. The physical pose is still produced by geometry, depth, CAD constraints, and cable continuity. This preserves R6 alignment while allowing practical robustness to texture, lighting, and visual clutter.

Option A is attractive as a minimal baseline but is too brittle under grip occlusion and cable ambiguity. Option B is easy to train in simulation but makes the physical pose a black-box regression target, which conflicts with the design principle and makes 2 mm-class precision hard to trust. Option D has the best theoretical alignment precision but is too expensive and too sensitive to local minima for the first implementation.

### 4.3 Recommended variant

| Variant | Description | Verdict |
| --- | --- | --- |
| C-1 | SAM2 fine-tuning + full Cosserat optimization | Keep as accuracy-oriented later variant. |
| C-2 | Light U-Net + DD-PINN or fast rod surrogate + light temporal filter | Good base, but underspecified for routing, uncertainty, and fallback. |
| C-2R | Routing-conditioned light segmentation + surrogate-assisted constrained rod fit + probabilistic fallback | **Recommended MVP path.** |
| C-3 | Isaac Sim semantic segmentation + full rod fit | Useful sim-only oracle baseline, but not sim-to-real compatible. |

C-2R should be implemented first because it preserves the low-latency spirit of C-2 while fixing four weak points:

- It uses routing and kinematics to shrink the visual search space.
- It treats confidence as a first-class output rather than a logging afterthought.
- It prevents a DD-PINN surrogate from becoming an unconstrained black box by adding a projection step back to the physical rod manifold.
- It defines explicit fallback states so silent estimator failure cannot leak into policy input.

### 4.4 C-2R design upgrade summary

| C-2 weakness | C-2R improvement | Expected effect |
| --- | --- | --- |
| Segmentation runs globally on 128² images without task context | Stage 0 proposes routing-conditioned ROIs and self-occlusion masks | Fewer false positives, lower compute, better small-object sensitivity |
| Cable segment identity can drift along the rod | Rod fitting uses routing-local priors and segment-index monotonicity | Reduces segment swaps and ±1-window ambiguity |
| DD-PINN surrogate may hallucinate physically invalid states | Surrogate output is projected through hard/soft constraints | Preserves R6 and makes failures inspectable |
| Confidence is not part of the contract | Every stage emits confidence and residuals | Enables ACCEPT / PREDICT / FALLBACK decisions |
| Fallback is vague | Stage 4 has explicit fallback state machine | Prevents silent use of stale or nominal poses |
| MVP-0 proves masks only | MVP-0A/0B also prove ROI and two-view visibility | Earlier detection of wrist-camera geometry issues |

### 4.5 C-2R core principle

C-2R should be treated as a **probabilistic physical estimator**, not as a deterministic perception module.

The estimator must compute:

```text
pose_estimate = argmin physical_residual(masked_depth, rod_model, clip_cad, priors)
confidence    = f(mask_quality, point_count, fit_residual, temporal_consistency, occlusion)
fallback_mode = gate(confidence, freshness, phase, safety_threshold)
```

This structure keeps the final 13D observation simple while preserving enough internal state to debug and train robustly.

---

## 5. C-2R stage specifications

### 5.1 Stage 0: kinematic prior and ROI proposal

#### Objective

Use information already available to the robot to reduce the visual search problem before segmentation.

Stage 0 does not estimate the final pose. It proposes where the estimator should look.

#### Inputs

| Input | Shape | Notes |
| --- | --- | --- |
| `joint_state` | `[W, J]` | Arm joint positions and velocities. |
| `body_state` | implementation-dependent | Used to compute wrist camera pose and gripper geometry. |
| `prev_cable_state` | `[W, 40, 7]` | Previous cable estimate, if available. |
| `routing_state` | `[W, ...]` | Current target segment and target clip index. |
| `nominal_clip_poses` | `[5, 7]` | Static prior from task config. |

#### Outputs

| Output | Shape | Purpose |
| --- | --- | --- |
| `roi_l`, `roi_r` | `[W, K, 4]` | Camera-space boxes for cable target region and target clip region. |
| `self_occlusion_mask_l/r` | `[W, 1, 128, 128]` | Pixels likely occupied by fingers, gripper, or robot body. |
| `target_segment_prior` | `[W, 40]` | Distribution centered on routing target with ±1 or wider support. |
| `clip_prior` | `[W, 5]` | One-hot or softened target clip prior. |

#### ROI construction

Compute ROIs from three sources:

1. **Nominal geometry projection**
   - Project nominal clip poses and previous cable estimate into each wrist camera.
   - Inflate boxes by uncertainty radius.

2. **Routing-local cable window**
   - For a target segment `i`, prioritize points near `i-1`, `i`, `i+1`.
   - Use a wider window when previous confidence is low.

3. **Robot self-occlusion prediction**
   - Project gripper/finger geometry into the wrist camera.
   - Mark expected robot-body pixels as self-occluded so Stage 1 does not confuse robot geometry with cable or clip.

#### Why Stage 0 improves C-2

The cable and clip are small in 128² wrist images. A global segmentation model wastes capacity on irrelevant pixels and can confuse gripper edges with cable edges. Stage 0 gives the model a task-conditioned view without violating R6 because it only constrains perception; it does not define the physical output.

### 5.2 Stage 1: segmentation + confidence

#### Objective

Convert RGB images into object masks:

- `cable_mask`
- `clip_mask[0..4]`
- `background_mask`
- `depth_valid_mask`
- `occlusion_likelihood`

#### Inputs

| Input | Shape | Notes |
| --- | --- | --- |
| `rgb_l`, `rgb_r` | `[W, 3, 128, 128]` | Wrist RGB images |
| `depth_l`, `depth_r` | `[W, 1, 128, 128]` | Used by later stages, optional for segmentation |
| `camera_pose_l`, `camera_pose_r` | `[W, 7]` | World-frame camera pose from body state |
| `roi_l`, `roi_r` | `[W, K, 4]` | Stage 0 proposals |
| `self_occlusion_mask_l/r` | `[W, 1, 128, 128]` | Stage 0 robot geometry projection |

#### Outputs

| Output | Shape | Notes |
| --- | --- | --- |
| `cable_prob` | `[W, C, H, W]` or `[W, 2, 128, 128]` | One binary map per camera |
| `clip_prob` | `[W, 2, 5, 128, 128]` | Instance masks for five clips |
| `depth_valid_prob` | `[W, 2, 1, 128, 128]` | Optional auxiliary head; improves RGB-D consistency |
| `occlusion_prob` | `[W, 2, 1, 128, 128]` | Predicts likely visually missing cable/clip areas |
| `mask_confidence` | `[W]` | Used by Stage 4 gating |

#### Model recommendation

Start with a small encoder-decoder rather than SAM2:

| Candidate | Use | Notes |
| --- | --- | --- |
| Light U-Net | Default MVP-0A | Simple, fast, easy to overfit and debug. |
| Fast-SCNN / BiSeNet-style model | Default if U-Net latency is too high | Better real-time trade-off. |
| SAM2 fine-tune | Later comparison | Higher memory, not ideal as first dependency. |
| Isaac Sim semantic labels | Oracle baseline only | Useful to bound Stage 2/3 errors, not real-transferable. |

#### Loss design

Use multi-task segmentation losses:

```text
L_stage1 =
  L_dice(cable)
+ L_focal(cable)
+ L_dice(clip_instances)
+ L_focal(clip_instances)
+ lambda_depth * L_bce(depth_valid)
+ lambda_occ   * L_bce(occlusion)
```

The clip class should be instance-aware from the beginning. Treating all five clips as a single class delays a hard identity problem into Stage 3.

#### Data randomization

MVP-0A should randomize:

- cable color and texture within realistic bounds;
- clip color/material within sim constraints;
- table/background appearance;
- lighting direction and intensity;
- camera exposure/noise;
- slight camera extrinsic perturbation;
- finger and gripper visibility;
- cable shape and routing phase.

The goal is not photorealism. The goal is to prevent the segmenter from keying on one brittle simulator artifact.

#### Initial implementation rule

Use synthetic labels from Isaac Sim for MVP-0A/0B. Do not hand-label real data before sim mask quality is proven.

### 5.3 Stage 2: confidence-weighted masked depth to point cloud

#### Objective

Back-project valid masked depth pixels into world-frame point clouds.

#### Required operations

1. Apply cable and clip masks to depth.
2. Reject invalid / saturated depth values.
3. Back-project using camera intrinsics.
4. Transform camera-frame points into world frame.
5. Merge left and right camera clouds.
6. Subsample or voxelize to a bounded point budget.
7. Attach per-point weights from segmentation probability, depth validity, and occlusion probability.

#### Outputs

| Output | Shape | Notes |
| --- | --- | --- |
| `cable_points_w` | ragged or `[W, N_cable, 3]` | Use padded representation for batched kernels. |
| `clip_points_w` | ragged or `[W, 5, N_clip, 3]` | Per-clip point sets. |
| `point_counts` | `[W]`, `[W, 5]` | Failure gating. |
| `point_weights` | matching point tensors | Used by Stage 3 robust fitting. |

#### Robust filtering

Stage 2 should apply:

- depth range clipping around projected ROI;
- statistical outlier removal in world frame;
- robot self-mask removal;
- confidence-weighted sampling rather than uniform sampling;
- optional voxelization to prevent dense background leakage from dominating.

#### Failure gate

If point count falls below threshold:

- cable: use prediction if last estimate is fresh;
- clip: fall back to nominal task config pose if the target clip is static and confidence is low;
- emit a diagnostic failure code.

### 5.4 Stage 3a: surrogate-assisted cable rod fitting

#### Objective

Estimate the full 40-segment cable state, then select the routing target segment.

#### Fit variables

For each world:

```text
q_cable = [
  seg_0_pos, seg_0_quat,
  ...
  seg_39_pos, seg_39_quat
]
```

#### Loss terms

The rod fit should minimize:

| Term | Purpose |
| --- | --- |
| Point-to-rod distance | Align visible cable surface / skeleton to observed point cloud. |
| Segment length consistency | Preserve known 40-segment rod geometry. |
| Continuity | Prevent segment jumps and swaps. |
| Bending regularization | Stabilize occluded and nearly straight portions. |
| Temporal prior | Prefer small changes from previous frame unless evidence is strong. |
| Routing-local weighting | Increase weight near current target segment and ±1 window. |
| Segment-index monotonicity | Prevent visible cable points from being assigned to physically impossible segment orderings. |

#### Recommended solver structure

Do not use DD-PINN as the final authority. Use it as a warm start:

```text
point_cloud + priors
        |
        v
DD-PINN / rod surrogate proposal
        |
        v
constraint projection
        |
        v
robust local refinement
        |
        v
40-seg cable state + residual + confidence
```

The projection/refinement step should enforce:

- segment length bounds;
- quaternion normalization and `w >= 0` canonicalization;
- continuity between neighboring segments;
- bounded per-frame displacement unless confidence is high;
- workspace bounds;
- optional target-window weighting.

#### Robust objective

Use a robust loss instead of plain L2:

```text
L_cable =
  rho(point_to_rod_distance, weights)
+ lambda_len  * segment_length_error
+ lambda_bend * bend_energy
+ lambda_temp * temporal_error
+ lambda_idx  * segment_order_error
+ lambda_roi  * target_window_error
```

Recommended robust loss candidates:

- Huber loss for moderate outliers;
- Tukey loss if false-positive points are common;
- trimmed least squares if mask leakage is severe.

#### Degeneracy handling

Cable orientation is ill-conditioned when a local section is nearly straight or only partially visible. In those cases:

- prioritize position accuracy over quaternion accuracy;
- derive tangent orientation from neighboring segments when possible;
- smooth quaternion output temporally;
- expose an orientation-confidence diagnostic.

#### Segment identity handling

The estimator must explicitly address segment identity. A cable point cloud alone does not label which surface point belongs to segment `i`.

Use a layered identity strategy:

1. Initialize from previous 40-seg state.
2. Use routing target to emphasize the local segment window.
3. Enforce monotonic ordering along the cable centerline.
4. Allow ±1 tolerance in evaluation but report exact-index and windowed metrics separately.
5. Detect segment swap by sudden changes in arc-length assignment.

### 5.5 Stage 3b: clip CAD fitting

#### Objective

Estimate five rigid clip poses from per-instance clip point clouds and known CAD geometry.

#### Recommended fit

Use a CAD-based rigid alignment:

1. initialize each clip at nominal `task_config.py` pose;
2. associate observed clip points with the CAD surface;
3. solve rigid transform with ICP or closed-form SVD where applicable;
4. constrain final pose by expected workspace and clip fixture assumptions;
5. select target clip using routing state.

#### Fallback

If a clip is fixed in the task and its nominal transform is trusted, the estimator may output the nominal pose when visual confidence is low. This fallback must be explicit in diagnostics; silent fallback is forbidden.

### 5.6 Stage 4: probabilistic temporal consistency and fallback gate

#### Objective

Reduce jitter and prevent single-frame segmentation failures from destabilizing policy input.

#### State machine

Stage 4 emits one of four states per world:

| State | Meaning | Policy obs source |
| --- | --- | --- |
| `ACCEPT_VISUAL` | Current visual estimate passes confidence and residual gates. | current Stage 3 estimate |
| `PREDICT_TEMPORAL` | Current visual estimate is weak, but previous estimate is fresh and dynamics are smooth. | predicted previous estimate |
| `FALLBACK_NOMINAL_CLIP` | Clip visual estimate failed, but nominal static clip pose is allowed. | nominal clip pose, with low-confidence flag |
| `FAIL_CLOSED` | Estimate is unsafe or stale. | no silent replacement; evaluator records failure, env integration must decide policy |

#### Confidence score

Compute a scalar confidence per target:

```text
conf =
  w_mask  * mask_confidence
+ w_pts   * point_count_score
+ w_fit   * exp(-fit_residual / tau_fit)
+ w_temp  * temporal_consistency
+ w_occ   * (1 - occlusion_score)
```

This score is a gating heuristic, not a calibrated probability in MVP-0 to MVP-2. Calibration can be added after residual data exists.

#### Update policy

```text
if current_confidence is high:
    accept current estimate
elif previous estimate is fresh and predicted residual is small:
    use predicted estimate
else:
    use conservative fallback and mark low confidence
```

#### Suggested update frequency

| MSA phase | Suggested estimator cadence |
| --- | --- |
| Approach / move | 5 Hz to 10 Hz |
| Close manipulation / grip | 20 Hz if available, otherwise every env step where camera is rendered |
| Static clip lookup | Lower frequency acceptable if clip fixtures are fixed |

The exact cadence should be measured after MVP-2. Avoid hard-coding frequency assumptions before profiling.

#### Smoothing rule

Apply smoothing only after fit validation. Smoothing should never hide a physically impossible Stage 3 output.

For positions:

```text
p_out = alpha * p_current + (1 - alpha) * p_previous
```

For quaternions:

```text
q_out = slerp(q_previous, q_current, alpha)
```

Use phase-dependent `alpha`:

| Phase | Suggested alpha |
| --- | ---: |
| fast approach | 0.7–0.9 |
| precise insertion / grip | 0.4–0.7 |
| low-confidence prediction | 0.0–0.3 |

---

## 6. Observation integration

### 6.1 Replacement mode

The default integration is **replacement**, not augmentation:

```text
obs[16:29] = pose_estimator(rgbd, joint_state, routing_state).as_obs_block()
```

This keeps the policy network shape unchanged and preserves compatibility with existing 42D checkpoints, subject to fine-tuning.

### 6.2 Error observation recomputation

The downstream error block `obs[30:41]` must be recomputed from estimated cable pose, not from ground truth.

```python
obs[30:33] = axis_angle(quat_diff(hand_R_quat, est_seg_quat))
obs[33:36] = hand_R_clamp_pos - est_seg_pos
obs[36:39] = axis_angle(quat_diff(hand_L_quat, est_seg_quat))
obs[39:42] = hand_L_clamp_pos - est_seg_pos
```

The estimator integration is incomplete unless this recomputation is switched to estimated pose. Otherwise the policy receives mixed GT and estimated observations.

### 6.3 Noise injection path

Before the real estimator is stable, training can emulate estimator noise:

```text
est_seg_pos  = gt_seg_pos  + Normal(0, sigma_pos)
est_seg_quat = perturb_quat(gt_seg_quat, sigma_ori)
```

Initial placeholder values:

| Parameter | Initial candidate | Final source |
| --- | ---: | --- |
| `sigma_pos` | 3 mm | measured MVP-2 / MVP-3 estimator residual |
| `sigma_ori` | 0.03 rad | measured MVP-2 / MVP-3 estimator residual |

The final noise distribution must be measurement-driven. Do not freeze these initial values as design truth.

### 6.4 Augmentation mode

Augmentation mode is deferred:

```text
obs_new = concat(obs_42d, est_13d, confidence_flags)
```

It may be useful for uncertainty-aware policies, but it breaks checkpoint compatibility and forces policy architecture changes. It is not recommended for the first implementation.

---

## 7. MVP roadmap

### 7.1 Phased implementation

| Phase | Scope | Exit criteria |
| --- | --- | --- |
| MVP-0A | Stage 0 ROI + Stage 1 segmentation; one camera; AC environment; sidecar evaluator | mIoU > 0.8; ROI recall > 0.95 for target cable/clip; no env mutation |
| MVP-0B | Add second camera and self-occlusion masking | target visibility improves over one-camera baseline; false positives on gripper/body decrease |
| MVP-1 | Stage 2 confidence-weighted point clouds; two cameras preferred | cable > 200 valid weighted points; each visible clip > 50 points; world overlay aligns with GT |
| MVP-2A | DD-PINN / surrogate warm-start only, no policy integration | surrogate proposal is fast and usually within projection convergence basin |
| MVP-2B | Add constrained projection + robust local refinement | target segment position error < 5 mm; orientation error < 0.05 rad on AC scenarios |
| MVP-2C | Add Stage 4 confidence/fallback state machine | ACCEPT/PREDICT/FALLBACK/FAIL_CLOSED labels correlate with actual residuals |
| MVP-3 | Replace `obs[16:29]` in AC only and recompute error obs | AC success reaches at least 90% of GT baseline |
| MVP-4 | Expand to IC / AR / Grip | all four skills reach at least 85% of GT baseline |

### 7.2 MVP-0A first ticket

Recommended first ticket:

```text
Implement a sidecar Stage 0 + Stage 1 segmentation evaluator for wrist RGB images.

Scope:
- Add a pose-estimator package shell.
- Add routing-conditioned ROI generation.
- Add robot self-occlusion mask projection.
- Add a light segmentation model wrapper.
- Generate sim labels for cable and five clips.
- Train or overfit on AC-only frames.
- Emit per-frame ROI, self-mask, object-mask visualizations, mIoU metrics, and ROI recall metrics.

Out of scope:
- env observation replacement
- policy fine-tuning
- Cosserat fitting
- clip ICP
- real robot data
```

### 7.3 MVP-2 split rationale

MVP-2 is intentionally split into three parts because cable pose estimation can fail in different ways:

| Subphase | What it proves | Why it should be separate |
| --- | --- | --- |
| MVP-2A | The surrogate can produce a plausible rod state quickly. | If this fails, DD-PINN is not useful even as a warm start. |
| MVP-2B | The constrained projection can make the state physically valid and accurate. | This is the R6-critical step; it must be tested independently. |
| MVP-2C | Confidence and fallback decisions match actual residuals. | A good mean residual is insufficient if failures are silent. |

### 7.4 Suggested files

| File | Purpose |
| --- | --- |
| `thread_isaac_lab/estimators/pose_estimator_v1.py` | top-level estimator interface |
| `thread_isaac_lab/estimators/roi_prior.py` | Stage 0 routing-conditioned ROI and prior generation |
| `thread_isaac_lab/estimators/self_occlusion.py` | gripper/body projection mask |
| `thread_isaac_lab/estimators/segmenter.py` | Stage 1 model wrapper |
| `thread_isaac_lab/estimators/depth_projector.py` | Stage 2 projection utilities |
| `thread_isaac_lab/estimators/cable_fit.py` | Stage 3a cable fitting |
| `thread_isaac_lab/estimators/rod_surrogate.py` | DD-PINN or fast rod warm-start model wrapper |
| `thread_isaac_lab/estimators/constraint_projection.py` | hard/soft physical projection layer |
| `thread_isaac_lab/estimators/clip_fit.py` | Stage 3b clip fitting |
| `thread_isaac_lab/estimators/temporal_gate.py` | Stage 4 state machine and smoothing |
| `thread_isaac_lab/scripts/train_segmenter.py` | Stage 1 training |
| `thread_isaac_lab/scripts/eval_pose_estimator_mvp0a.py` | MVP-0A evaluator |
| `thread_isaac_lab/scripts/eval_pose_estimator_mvp0b.py` | MVP-0B two-camera/self-occlusion evaluator |
| `thread_isaac_lab/scripts/eval_pose_estimator_mvp2.py` | pose residual evaluator |

Keep file names provisional until repository conventions are checked.

---

## 8. Performance budget

### 8.1 Expected runtime

| Component | Expected cost at W=32, C=2, 128² | Notes |
| --- | ---: | --- |
| Existing camera rendering | ~28.6 ms / step | Existing benchmark; approximately 6% step overhead. |
| Stage 1 light U-Net | ~10–15 ms / step | Needs profiling; depends on batch layout. |
| Stage 2 depth projection | ~1–2 ms / step | Warp kernel target. |
| Stage 3a cable fit | ~3–5 ms / step if surrogate is used | Full nonlinear optimization may exceed budget. |
| Stage 3b clip fit | ~1–2 ms / step | CAD alignment, small object count. |
| Stage 4 temporal filter | <1 ms / step | Mostly thresholding and interpolation. |
| Estimator subtotal | ~15–25 ms / step | Design target, not measured truth. |

### 8.2 Budget rule

The estimator should be treated as acceptable only if:

```text
camera_rendering_overhead + estimator_overhead <= approximately 10–12% total step overhead
```

If Stage 3 fitting exceeds budget, priority order for mitigation is:

1. reduce estimator cadence;
2. restrict fitting to routing-local cable windows;
3. use previous-frame warm start;
4. switch full optimization to a surrogate;
5. defer obs replacement and keep sidecar-only evaluation.

### 8.3 GPU allocation notes

The design assumes the existing simulation/training allocation remains primary. Estimator integration must not starve the active Phase 5 training queue. Any implementation ticket should include an explicit GPU claim and process-slot plan.

---

## 9. Validation strategy

### 9.1 Offline estimator metrics

Compare estimator output against simulator ground truth without involving policy:

| Metric | Definition | Gate |
| --- | --- | --- |
| Cable target position error | `||est_seg_pos - gt_seg_pos||` | < 5 mm for MVP-2 |
| Cable target orientation error | quaternion angular distance | < 0.05 rad for MVP-2 |
| Clip target position error | `||est_clip_pos - gt_clip_pos||` | < 3–5 mm initially |
| Clip orientation error | quaternion angular distance | task-dependent |
| Mask mIoU | semantic/instance mask overlap | > 0.8 for MVP-0A |
| Jitter | frame-to-frame estimate variance under static scene | must not destabilize error obs |
| Failure recovery | frames to recover after mask dropout | characterize before policy use |

### 9.2 Policy-level metrics

Only after offline gates pass:

| Skill | Required test |
| --- | --- |
| AC | first integration target; success ≥ 90% of GT baseline |
| IC | test after AC because insertion-like tasks amplify pose error |
| AR | test multi-segment routing and L/R target selection |
| Grip | test occlusion-heavy regime and temporal fallback |

### 9.3 Ablations

Run these ablations before declaring Option C-2R successful:

| Ablation | Purpose |
| --- | --- |
| GT mask + Stage 2/3 | isolates segmentation error |
| predicted mask + GT depth | isolates depth/projection error |
| predicted mask + predicted depth path | full visual pipeline |
| one camera vs two cameras | measures benefit of stereo-like coverage |
| no temporal filter vs temporal filter | measures jitter and recovery trade-off |
| routing-local fit vs full 40-seg fit | measures performance/accuracy trade-off |
| no ROI vs Stage 0 ROI | measures whether routing-conditioned perception actually improves masks |
| no self-occlusion mask vs self-occlusion mask | measures false-positive reduction around gripper/body |
| surrogate only vs surrogate + projection | verifies that DD-PINN is not bypassing physical constraints |
| confidence gate disabled vs enabled | measures silent-failure reduction |

### 9.4 Failure classification

Every evaluator run should bucket failures:

| Code | Meaning |
| --- | --- |
| `SEG_EMPTY_CABLE` | cable mask missing or too small |
| `SEG_EMPTY_CLIP` | target clip mask missing or too small |
| `DEPTH_INVALID` | depth values invalid after masking |
| `FIT_DIVERGED` | cable/clip fit residual too high |
| `OCCLUDED_TARGET` | target segment or clip is visually occluded |
| `TEMPORAL_STALE` | prediction used beyond allowed freshness |
| `ROUTING_MISMATCH` | target index inconsistent with estimator output |
| `SEGMENT_SWAP` | arc-length / segment-index assignment jumps implausibly |
| `SURROGATE_INVALID` | DD-PINN proposal violates rod constraints before projection |
| `PROJECTION_FAILED` | constrained projection cannot recover a valid rod state |
| `CONFIDENCE_MISCALIBRATED` | high confidence but high residual in sim-evaluable data |

Failure labels matter because the main risk is not average error; it is rare, unobserved failures entering policy input silently.

---

## 10. Risk register

| Risk | Severity | Why it matters | Mitigation |
| --- | --- | --- | --- |
| Cable target is occluded by gripper | High | Policy may receive stale or wrong target pose during the most precise phase. | Temporal prior, two cameras, routing-local confidence, grip-specific validation. |
| Straight cable section creates orientation degeneracy | Medium | Segment position may be correct while quaternion is unstable. | Tangent smoothing, confidence score, neighbor-derived orientation. |
| Segmentation works in sim but not real | High for sim-to-real | Stage 1 is the main domain-gap surface. | Domain randomization, light model first, real calibration dataset later. |
| Estimator overhead breaks W=32 throughput | Medium | Vision stack could slow RL iteration. | Sidecar first, cadence control, routing-local fitting, surrogate Stage 3. |
| Mixed GT and estimated obs leak into training | High | Policy evaluation becomes invalid. | Integration test that asserts all pose-dependent obs slices use the same pose source. |
| Silent fallback hides estimator failure | High | Policy may appear stable while estimator is not actually solving the task. | Mandatory diagnostics and failure counters. |
| Pure NN shortcut creeps into physical pose | Medium | Violates R6 and reduces interpretability. | Restrict NN to segmentation unless Rs explicitly approves a different principle. |

---

## 11. Open decisions for Rs

### OQ-1: Option approval

Recommended decision:

```text
Approve Option C-2R as target design.
```

Alternative decisions:

- Option A if implementation speed is valued over precision and occlusion robustness.
- Option B only if R6 is relaxed explicitly.
- Option D only as a later refinement or offline oracle.
- Original C-2 if the additional ROI/confidence/fallback machinery is considered too much for the first pass.

### OQ-2: MVP scope

Recommended decision:

```text
Approve staged MVP, starting with MVP-0A only, then MVP-0B if one-camera masks are not enough under occlusion.
```

Avoid authorizing MVP-3 immediately. Full obs replacement before segmentation and point-cloud gates pass creates unnecessary rollback risk.

### OQ-3: Implementation timing

Recommended decision:

```text
Keep this design parked until Phase 5-1 / current RL priorities clear or Vision Stack is un-parked.
```

MVP-0A may run in parallel only if GPU/process-slot contention is explicitly resolved.

### OQ-4: Noise distribution

Recommended decision:

```text
Use placeholder noise only for early robustness experiments; set final DR noise from measured estimator residuals.
```

Initial placeholder:

- `sigma_pos = 3 mm`
- `sigma_ori = 0.03 rad`

### OQ-5: Sim-to-real PoC timing

Recommended decision:

```text
Defer real-robot PoC until MVP-4 or until Vision Stack Roadmap is un-parked.
```

---

## 12. Implementation checklist

Before any code lands:

- [ ] Confirm Option C-2R approval.
- [ ] Confirm MVP-0A scope only.
- [ ] Confirm no mutation to env obs path in MVP-0A.
- [ ] Confirm GPU and process-slot allocation.
- [ ] Confirm synthetic segmentation label source.
- [ ] Confirm evaluation dataset generation command.
- [ ] Confirm output artifact format for mask visualizations.

Before env integration:

- [ ] MVP-0A ROI + mask gate passed.
- [ ] MVP-0B two-camera/self-occlusion gate passed, if required.
- [ ] MVP-1 point-cloud gate passed.
- [ ] MVP-2A surrogate warm-start gate passed.
- [ ] MVP-2B projection/refinement residual gate passed.
- [ ] MVP-2C confidence/fallback gate passed.
- [ ] Error obs recomputation path implemented.
- [ ] Diagnostics are emitted and logged.
- [ ] Fallback behavior is explicit and counted.
- [ ] GT-vs-est source mixing test passes.

Before policy fine-tuning:

- [ ] Offline estimator residual distribution characterized.
- [ ] DR noise distribution set from measured residuals.
- [ ] AC-only integration tested.
- [ ] Baseline GT observation run re-confirmed.
- [ ] Estimator-on policy run compared against baseline.

---

## 13. Revised document status

This v2 version turns the original research-heavy proposal into an execution-oriented design contract and upgrades C-2 into C-2R:

- recommended option is explicit;
- implementation is gated rather than implied;
- routing-conditioned ROI and self-occlusion priors are added before segmentation;
- estimator inputs, outputs, diagnostics, and module boundaries are defined;
- DD-PINN is constrained to warm-start duty and cannot silently define physical pose;
- confidence, residuals, and fallback state are part of the estimator contract;
- obs replacement and dependent error-observation recomputation are specified;
- MVP gates are measurable;
- failure modes are first-class diagnostics;
- Rs decisions are separated from implementation details.

The design remains a proposal. The next action is an Rs decision on Option C-2R, MVP-0A scope, and implementation timing.

---

## Appendix A: Glossary

| Term | Meaning |
| --- | --- |
| MSA | Multi-Skill Agent, the 42D-observation / 12D-action policy stack across AC, IC, AR, and Grip. |
| VBD | Vertex Block Descent, Newton solver path used for cable simulation. |
| DLO | Deformable Linear Object, here primarily the cable. |
| DR | Domain Randomization. |
| DAPG | Demo Augmented Policy Gradient. |
| R6 | Observation Grounding design rule: learned decoding is allowed, but physical quantities must remain physically constrained. |
| ICP | Iterative Closest Point, used for geometry-based rigid fitting. |
| DD-PINN | Domain-Decoupled Physics-Informed Neural Network, a candidate fast surrogate for rod fitting. |
| GT | Ground truth, here simulator state such as Newton `body_q`. |
| W | Number of parallel worlds. |
| C | Number of cameras. |

## Appendix B: Source lineage

This v2 design consolidates and restructures the original v1 material from:

- Vision Pipeline / R6 observation grounding;
- Camera Backend precedent;
- Vision Stack Roadmap;
- DLO Research Survey;
- LL-VisualObs-CameraSystem camera benchmark;
- RL-Routing-Design observation contract;
- THREAD-specific Newton VBD and MSA constraints.

External research references retained from the original design include:

- [Deep Learning-Based Object Pose Estimation: A Comprehensive Survey](https://github.com/CNJianLiu/Awesome-Object-Pose-Estimation)
- [GoTrack: Generic 6DoF Object Pose Refinement and Tracking](https://github.com/facebookresearch/gotrack)
- [Pose-Perceptive Convolution](https://pmc.ncbi.nlm.nih.gov/articles/PMC12845661/)
- [Enhanced RGB-D Feature Extraction for 6D Pose Estimation](https://www.nature.com/articles/s41598-025-34757-y)
- [R3M: A Universal Visual Representation](https://openreview.net/forum?id=tGbpgz6yOrI)
- [Adaptive MPC of Soft Continuum Robot using PINN + Cosserat](https://arxiv.org/html/2508.12681v1)
- [Cosserat Rods / Elastica](https://www.cosseratrods.org/)
- [DREAM Camera-to-Robot Pose](https://www.ri.cmu.edu/app/uploads/2020/03/dream_icra2020_final.pdf)
- [Training-Free Robot Pose Estimation](https://arxiv.org/html/2512.06017v1)
