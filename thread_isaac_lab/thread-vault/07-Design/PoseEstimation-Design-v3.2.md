---
status_ledger: 00-DESIGN-STATUS-LEDGER.md  # authoritative success/failure status SSOT
title: Pose Estimation Design v3.2 — Minimum patch to v3.1 (arithmetic normalization + module boundary + FAIL_CLOSED storage)
created: "2026-04-25T07:55:00+09:00"
updated: "2026-04-25T07:55:00+09:00"
status: "Minimum patch — supersedes v3.1 for sections listed in §1; v3 remains parent"
owner: "CC#4 / Pose Estimation Research"
supersedes: "[[PoseEstimation-Design-v3.1]] (sections listed in §1.2)"
parent: "[[PoseEstimation-Design-v3]]"
parent_patch: "[[PoseEstimation-Design-v3.1]]"
rs_directive: "Rs 2026-04-25 07:55 — v3.2 minimum patch: 1) 42D→47D normalize to 45D→50D globally 2) Appendix E 45D→50D replacement 3) regime/conf normalizer epsilon-variance forbidden 4) input_adapter/estimator_core boundary explicit 5) FAIL_CLOSED training loss mask storage requirement"
tags:
  - design
  - vision
  - pose-estimation
  - minimum-patch
  - post-env-verification
---

# Pose Estimation Design v3.2 — Minimum patch

> **⚠ CURRENT HEAD — renewal batch B, 2026-07-11 (banner-only; content edit-frozen):** this is the **PARKED head** of the pose-estimation design stock (`00-DESIGN-STATUS-LEDGER.md:50` = ⏸ **PARKED (head)**, minimum patch over v3.1). **UNVALIDATED** — vision (L1.A) is **not started**; gated (P0-KILL). **Composite-reading contract (verbatim, frontmatter `status:` + §1.1):** *"open v3 + v3.1 + v3.2 together. v3.2 supersedes v3.1 for listed sections only"* + *"v3 remains parent"* — v3.2 supersedes v3.1 **only for the sections listed in §1.2**; all other sections defer to v3.1, and **v3 remains the parent base**. Lineage: v1→v2→v3→v3.1→**v3.2 (head)**. LEDGER pointers: v3.2 `:50` / v3.1 `:51` / v3 `:52` / v2 `:53` / v1 `:54`. Status SSOT = `00-DESIGN-STATUS-LEDGER.md`.

## 1. Patch scope

### 1.1 Parent documents

- **v3** (parent, post-debate revision, 1416 lines): base design
- **v3.1** (patch to v3, 1186 lines after §15 addendum): 12 Rs-feedback improvements
- **v3.2** (this patch): 5-item minimum correction after env verification surfaced arithmetic errors + module-boundary gaps

Reader: open v3 + v3.1 + v3.2 together. v3.2 supersedes v3.1 for listed sections only.

### 1.2 Sections modified in v3.2

| Item | Purpose | v3.1 sections affected | v3.2 location |
| --- | --- | --- | --- |
| 1 | **Global normalize 42D→47D → 45D→50D** | §0.3, §2.3, §2.4, §6.4, Appendix E §E.1-E.7, §13 revision, §15 (already partial) | §2 below (search-replace manifest) |
| 2 | **Appendix E full replacement** with 45D→50D | v3.1 Appendix E (all sub-sections) | §3 below (full Appendix E v3.2) |
| 3 | **regime/conf normalizer: epsilon-variance forbidden**, use no-normalization (raw pass-through) or unit variance | v3.1 Appendix E §E.3 | Integrated into §3 Appendix E v3.2 |
| 4 | **input_adapter / estimator_core boundary explicit** | Appendix D P2 input boundary | §4 below + Appendix H (NEW) |
| 5 | **FAIL_CLOSED training loss mask storage requirement** | §7 (P7 training/eval separation) + Appendix F (dataset) | §5 below + Appendix I (NEW) |

### 1.3 Parallelism / overlap (Rs question)

- Items 1+2+3: **overlap** (normalization arithmetic / Appendix E common topic) → executed as single consolidation
- Item 4: **independent** → separate section + new Appendix H
- Item 5: **independent** → separate section + new Appendix I

---

## 2. Item 1 — Global arithmetic normalization (42D→47D → 45D→50D)

### 2.1 Trigger

v3.1 §15 addendum identified that base model input is 45D unified (not 42D), therefore augmented = 50D (not 47D). §15 provided corrections in §15.2, §15.3, §15.4, §15.5, §15.6. Residual 42D/47D references remain in v3.1 body sections outside §15. v3.2 Item 1 completes the global normalization.

### 2.2 Search-replace manifest (v3.1 → v3.2 supersession)

Apply these replacements when reading v3.1:

| v3.1 occurrence | v3.2 replacement | Scope |
| --- | --- | --- |
| "obs 42D" (referring to base model input shape) | "obs 45D (42D content + 3D zero pad)" | doc-wide |
| "42D → 47D" (augmented obs contract) | "45D → 50D" | §0.3, §2.4, §6.4 |
| "obs[42:46] regime one-hot" | "obs[45:49] regime one-hot" | §6.4 |
| "obs[46] confidence scalar" | "obs[49] confidence scalar" | §6.4 |
| "47D" (anywhere referring to AC augmented shape) | "50D" | §0.3, §2.3, §2.4, §6.1, §6.4, §6.5, §11 OQ-2, §13, Appendix E |
| "42D running mean/std" | "45D running mean/std" | Appendix E §E.3 |
| "new 5D (one-hot + conf)" | "new 5D (one-hot + conf)" — retained (count unchanged) | Appendix E §E.3 |
| "Linear(42, hidden_dim)" | "Linear(45, hidden_dim)" | Appendix E §E.4 |
| "Linear(47, hidden_dim)" | "Linear(50, hidden_dim)" | Appendix E §E.4 |
| "in_features == 42" | "in_features == 45" | Appendix E §E.4 |
| "weight.data[:, :42]" | "weight.data[:, :45]" | Appendix E §E.4 |
| "weight.data[:, 42:47] = 0.0" | "weight.data[:, 45:50] = 0.0" | Appendix E §E.4 |

### 2.3 v3.1 §0.3 MVP-3 row (patch)

v3.1 §0.3 MVP-3 row:

```text
Before: Replace AC obs[16:30] in env, recompute error obs, augmented obs contract (42D → 47D: 4 state bits + 1 confidence scalar)
After:  Replace AC obs[16:30] in env, recompute error obs, augmented obs contract (45D → 50D: 4 state bits + 1 confidence scalar; base model input was already 45D with zero pad at [42:45])
```

### 2.4 v3.1 §2.3 Primary acceptance criteria (patch)

v3.1 §2.3 table row "Observation compatibility":

```text
Before: AC-only MVP-3: obs[16:30] 14D + obs[30:42] 12D recomputed from est pose + 4D state one-hot + 1D confidence = 47D augmented policy obs
After:  AC-only MVP-3: obs[16:30] 14D + obs[30:42] 12D recomputed from est pose + obs[42:45] 3D zero pad (structural) + 4D state one-hot at [45:49] + 1D confidence at [49] = 50D augmented policy obs
```

### 2.5 v3.1 §2.4 Shape row (patch)

```text
Before: "preserves 42D contract"            (v2 superficial claim)
        "Expands AC obs from 42D → 47D"     (v3 correction)
After:  "Expands AC obs from 45D → 50D"     (v3.2 correction, base was already 45D unified)
```

### 2.6 v3.1 §6.4 Augmented obs structure (patch)

```text
AC policy obs at MVP-3:
  [0:16]   MSA proprio (existing 45D content, unchanged)
  [16:30]  est_seg + est_clip pose (14D, estimator output)
  [30:42]  recomputed error obs (12D, from est pose)
  [42:45]  structural zero pad (existing 45D content, unchanged)
  [45:49]  regime one-hot: [ACCEPT, PREDICT, FALLBACK, FAIL_CLOSED]
  [49]     confidence scalar in [0, 1]

Total: 50D
```

### 2.7 v3.1 §11 OQ-2 (patch)

OQ-2 body unchanged (AC-only MVP-0A→MVP-3; MVP-4 deferred pending OQ-5). Inline references to "47D" replaced with "50D".

### 2.8 v3.1 §13 revision entry (patch)

Add "42D→47D" correction note to v3.2 revision history:

```text
v3 claim: 42D unified → 47D augmented
v3.1 §15 correction: base is 45D unified → 50D augmented (content from env verification)
v3.2 Item 1 completion: global residual 42D/47D references in v3.1 body replaced with 45D/50D
```

---

## 3. Item 2 + Item 3 — Appendix E full replacement (Policy migration 45D → 50D, epsilon-variance forbidden)

This section fully replaces v3.1 Appendix E.

### Appendix E (v3.2): Policy migration 45D → 50D

#### E.1 Scope

AC skill only (MVP-3 integration target per v3 §6.1 AC-only scoping). AR / Grip-dual / IC deferred per OQ-5.

#### E.2 Starting state

- Baseline: converged AC policy trained on GT obs 45D (base model input; `45D = 42D content + 3D zero pad at [42:45]`)
- Checkpoint: end-of-training baseline (not mid-training)
- Architecture: PPO with MLP actor + critic, obs dim 45 → actions 12 + value scalar

#### E.3 Obs normalizer migration (with epsilon-variance forbidden, Item 3)

THREAD uses RSL-RL running observation normalizer (mean / std per dim). v3.1 proposed epsilon variance (0.01²) for new regime + confidence dims. **v3.2 forbids** epsilon variance and specifies a correct handling:

```python
def migrate_obs_normalizer_45_to_50(old_normalizer_45):
    """Extend 45D running stats to 50D for AC augmented obs.

    Rules (v3.2):
    - Inherit old 45D running mean/var for dims [0:45] (unchanged)
    - Regime one-hot dims [45:49] and confidence dim [49]:
        NOT normalized (raw pass-through) — these are bounded categorical / bounded [0,1]
        NEVER use epsilon variance (z-score explodes on small deviations from init)
    - Normalization is applied to dims [0:45] only; dims [45:50] pass through untouched
    """
    from rsl_rl.modules.normalizer import EmpiricalNormalization

    new_normalizer_50 = EmpiricalNormalization(
        shape=(50,),
        until=1e8,
        normalize_dims=list(range(45)),  # dims 45-49 NOT normalized
    )

    # Inherit old 45D running stats
    new_normalizer_50.mean[:45] = old_normalizer_45.mean
    new_normalizer_50.std[:45] = old_normalizer_45.std
    new_normalizer_50.count = old_normalizer_45.count

    # Dims 45-49: pass-through identity (mean=0, std=1 equivalent, no update)
    new_normalizer_50.mean[45:50] = 0.0
    new_normalizer_50.std[45:50] = 1.0
    new_normalizer_50.update_dims = list(range(45))  # only update first 45

    return new_normalizer_50
```

**Forbidden pattern (from v3.1 §15.3):**

```python
# FORBIDDEN (v3.2 Item 3):
new_normalizer.var[45:49] = 0.01 ** 2  # epsilon variance
# Reason: any deviation from init (e.g., regime != ACCEPT) produces z-score ~100x input
# Reason: policy sees huge normalized deviation for small input change
# Reason: collapses exploration / destabilizes value function early in finetune
```

**Rationale:**

- Regime one-hot: categorical, bounded [0, 1] per dim, sum = 1. Mean/std statistics are not meaningful. Raw one-hot is the natural input representation.
- Confidence scalar: bounded [0, 1], semantic interpretation is direct (1 = fully trusted, 0 = fully untrusted). Normalizing would require known distribution (uniform? gaussian?) which is not assumed. Raw pass-through preserves semantic interpretability.
- Both are policy inputs where the raw value IS meaningful; normalization is a concept mismatch.

#### E.4 Network first-layer weight migration (v3.2, 45D → 50D)

```python
def migrate_first_layer_45_to_50(old_first_layer: torch.nn.Linear):
    """Expand first-layer input dim from 45 to 50 with zero-init for new dims (v3.2)."""
    assert old_first_layer.in_features == 45, \
        f"Expected 45D input (base model input), got {old_first_layer.in_features}"
    hidden_dim = old_first_layer.out_features
    new_first_layer = torch.nn.Linear(50, hidden_dim)

    # Copy old 45D weights
    new_first_layer.weight.data[:, :45] = old_first_layer.weight.data

    # Zero-init new 5D weights (4 regime one-hot + 1 confidence)
    new_first_layer.weight.data[:, 45:50] = 0.0

    # Bias unchanged
    new_first_layer.bias.data = old_first_layer.bias.data.clone()

    return new_first_layer


def migrate_policy_45_to_50(baseline_ckpt_path, new_ckpt_path):
    """Full policy migration 45D → 50D (v3.2, supersedes v3.1 §15.3)."""
    sd = torch.load(baseline_ckpt_path)

    for first_layer_key in ('actor.0.weight', 'critic.0.weight'):
        old_weight = sd[first_layer_key]
        assert old_weight.size(1) == 45, \
            f"Expected 45D input, got {old_weight.size(1)}"
        hidden_dim = old_weight.size(0)
        new_weight = torch.zeros(hidden_dim, 50)
        new_weight[:, :45] = old_weight           # copy existing
        new_weight[:, 45:50] = 0.0                # zero-init new 5D
        sd[first_layer_key] = new_weight

    torch.save(sd, new_ckpt_path)
```

#### E.5 Initial behavior guarantee (v3.2)

At step 0 after migration, with obs = `[45D_existing_content, one_hot_ACCEPT, conf=1.0]`:

- first_layer(obs)[:, :45] = old_layer[:, :45] @ existing_45D (same as baseline)
- first_layer(obs)[:, 45:50] = 0 @ [1, 0, 0, 0, 1] = 0 (zero contribution)

Total first-layer activation = baseline activation. Policy output and value output are preserved bit-identical when regime = ACCEPT + conf = 1.0.

**Crucial v3.2 invariant:** since regime/confidence dims are NOT normalized (per E.3), the raw input `[1, 0, 0, 0, 1.0]` passes through unchanged to the weight matrix's zero-init columns. Policy's initial behavior is bit-identical to 45D baseline even under the augmented obs contract.

#### E.6 Rollback criterion (unchanged from v3.1)

```text
Monitor during MVP-3 fine-tune:
  value_loss moving average over 20 iters

If value_loss > 3 x baseline_end_value_loss at iter 20:
  abort fine-tune
  rollback to baseline checkpoint
  fresh-start with migration re-applied
  investigate: likely DR distribution mismatch or estimator residual too high
```

#### E.7 Action scale / reset noise / reward (unchanged)

Migration does NOT modify action scale, reset noise, reward function, env dynamics. Only:
- obs dim 45 → 50
- first-layer in_features 45 → 50
- running normalizer shape (45,) → (50,) with update_dims restricted to [0, 45)

Env changes: obs assembler appends 5D regime+conf to the existing 45D tensor. No content change to [0, 45).

#### E.8 Summary (v3.2)

Key differences vs v3.1 Appendix E:
- arithmetic: 42→45, 47→50 throughout
- normalizer: epsilon variance forbidden, raw pass-through for regime+conf
- invariant: initial bit-identical behavior preserved under raw pass-through

---

## 4. Item 4 — input_adapter / estimator_core boundary explicit

### 4.1 Trigger

v3.1 Appendix D specified `EstimatorInputs` vs `EstimatorLabelsForEvalOnly` but did not detail the module boundary BETWEEN input adaptation (sensor → tensor) and estimator core (tensor → pose). This left an impl gap: where does `WristCameraManager` output handoff end and `PoseEstimatorV1.forward` begin? v3.2 Item 4 makes this explicit via a new Appendix H.

### 4.2 Summary

See **Appendix H** (below). Two distinct modules:

| Module | Role | Must NOT do |
| --- | --- | --- |
| `PoseEstimatorInputAdapter` | Sensor → tensor conversion (RGB-D, camera transforms, joint state, prev_estimate marshalling) | Pose inference, learning, NN forward |
| `PoseEstimatorCore` | Tensor → PoseEstimate14D + RegimeState (stages 0-4) | Sensor read, camera buffer management |

### 4.3 Enforcement

- Type enforced via separate signatures
- Import boundary: estimator_core MUST NOT import from `wrist_camera_manager` or newton directly; it receives pre-digested tensor inputs only
- Unit test: attempting to import `newton` or `wrist_camera_manager` from `estimator_core` raises

---

## 5. Item 5 — FAIL_CLOSED training loss mask storage requirement

### 5.1 Trigger

v3.1 §8 (P7) described FAIL_CLOSED training vs eval separation with "Option C" recommended (PREDICT for K=20, then terminate, mask terminal from policy loss). But v3.1 did not specify HOW the mask is physically stored and accessed during policy training. RSL-RL uses a rollout storage buffer; if the mask is not first-class in the storage schema, impl will silently drop it or require workaround hacks.

v3.2 Item 5 makes storage schema explicit via a new Appendix I.

### 5.2 Summary

See **Appendix I** (below). Requirements:

- Extend rollout storage with `policy_update_mask: Bool[T, W]` per transition
- PPO loss multiplies advantage / value error by mask
- FAIL_CLOSED transitions: `policy_update_mask = False`
- Normal transitions: `policy_update_mask = True`
- GAE computation: mask must NOT break temporal credit assignment → specific handling required

### 5.3 Implementation feasibility answer (Item 5 requirement)

Is this implementable? **YES, with 2 architectural requirements:**

1. **Rollout storage schema extension**: Add `policy_update_mask` field to `rsl_rl.storage.RolloutStorage` (or THREAD's wrapper). Cost: ~20 LOC + one storage buffer extra.
2. **GAE computation modification**: Mask must NOT interrupt bootstrapping. See Appendix I §I.3 for correct handling.

Both are modular patches to existing RSL-RL. No core RL algorithm change. Feasibility: **implementable at MVP-3 + ~2 days of impl/test effort**.

---

## Appendix H: Estimator Input Adapter / Core Boundary (v3.2, new)

### H.1 Module layering

```text
┌────────────────────────────────────────────────────┐
│ THREAD Environment (newton_approach_cable_env etc) │
│  - Newton body_q, camera, joint state              │
└────────────────────┬───────────────────────────────┘
                     │ raw sim state
                     │ (owned by env)
                     ▼
┌────────────────────────────────────────────────────┐
│ WristCameraManager                                 │
│  - SensorTiledCamera lifecycle                     │
│  - body_q → camera transform                       │
│  - render RGB-D                                    │
└────────────────────┬───────────────────────────────┘
                     │ extras["visual_obs"] tensors
                     │ (owned by WristCameraManager)
                     ▼
┌────────────────────────────────────────────────────┐
│ PoseEstimatorInputAdapter  (v3.2 new module)       │
│  - RGB-D tensors ← WristCameraManager.color/depth  │
│  - camera_pose ← body_q[wrist_L/R] + LOCAL_POS     │
│  - joint_state ← env.joint_q / joint_qd            │
│  - gripper_geometry ← static mesh + body_q[fingers]│
│  - routing_state ← orchestrator provided           │
│  - previous_estimate ← self (carried across steps) │
│  - assembles: EstimatorInputs dataclass            │
└────────────────────┬───────────────────────────────┘
                     │ EstimatorInputs (v3.1 Appendix D)
                     ▼
┌────────────────────────────────────────────────────┐
│ PoseEstimatorCore  (v3.2 renamed from v3.1         │
│                    `PoseEstimatorV1`)              │
│  - Stage 0: ROI / self-occlusion                   │
│  - Stage 1: segmentation NN forward                │
│  - Stage 2: depth back-projection (Warp kernel)    │
│  - Stage 3a: rod fit + projection + refinement     │
│  - Stage 3b: clip CAD ICP                          │
│  - Stage 4: temporal gate + state machine          │
│  - Outputs: PoseEstimate14D + RegimeState          │
└────────────────────┬───────────────────────────────┘
                     │ PoseEstimate14D + RegimeState
                     ▼
┌────────────────────────────────────────────────────┐
│ ObsAssembler (env wrapper)                         │
│  - obs[16:30] replaced                             │
│  - obs[30:42] recomputed                           │
│  - obs[45:50] appended (regime + conf)             │
└────────────────────────────────────────────────────┘
```

### H.2 Module responsibilities

| Module | Owns | Depends on | Must NOT depend on |
| --- | --- | --- | --- |
| `WristCameraManager` | SensorTiledCamera + transform | newton, warp | `PoseEstimator*`, env obs |
| `PoseEstimatorInputAdapter` | `EstimatorInputs` assembly | `WristCameraManager` output tensors, env `body_q` for camera/joint only | Pose inference, NN forward |
| `PoseEstimatorCore` | Stages 0-4 + PoseEstimate14D | `EstimatorInputs` dataclass only | `WristCameraManager`, `newton`, env obs, Newton body_q |

### H.3 Import boundary enforcement

`PoseEstimatorCore` module MUST NOT import:
- `newton`
- `thread_isaac_lab.envs.wrist_camera_manager`
- `thread_isaac_lab.envs.newton_approach_cable_env` (or any env)

This is enforced via a lint test:

```python
# thread_isaac_lab/tests/test_estimator_module_boundary.py
import ast
import pathlib
import pytest

ESTIMATOR_CORE_ROOT = pathlib.Path("thread_isaac_lab/estimators/core/")

FORBIDDEN_IMPORTS = {
    "newton",
    "thread_isaac_lab.envs.wrist_camera_manager",
    "thread_isaac_lab.envs.newton_approach_cable_env",
    "thread_isaac_lab.envs.newton_aerial_regrasp_env",
    "thread_isaac_lab.envs.newton_grip_env",
    "thread_isaac_lab.envs.newton_insert_clip_env",
}


@pytest.mark.parametrize("py_file", list(ESTIMATOR_CORE_ROOT.rglob("*.py")))
def test_no_forbidden_import(py_file):
    tree = ast.parse(py_file.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in (node.names if isinstance(node, ast.Import) else ()):
                assert alias.name not in FORBIDDEN_IMPORTS, \
                    f"{py_file}: forbidden import '{alias.name}'"
            if isinstance(node, ast.ImportFrom):
                assert node.module not in FORBIDDEN_IMPORTS, \
                    f"{py_file}: forbidden from-import '{node.module}'"
```

### H.4 API signatures

```python
# thread_isaac_lab/estimators/input_adapter.py

class PoseEstimatorInputAdapter:
    def __init__(self, wrist_camera_manager, env_kinematics):
        self._cam = wrist_camera_manager
        self._env = env_kinematics

    def assemble(
        self,
        routing_state: RoutingState,
        previous_estimate: PoseEstimate14D | None,
    ) -> EstimatorInputs:
        """Produce EstimatorInputs from current camera + robot state.

        This is the ONLY place that bridges raw env state and the estimator core.
        """
        return EstimatorInputs(
            rgb_l=self._cam.rgb_tensor[:, 0, ...],
            rgb_r=self._cam.rgb_tensor[:, 1, ...],
            depth_l=self._cam.depth_tensor[:, 0, ...],
            depth_r=self._cam.depth_tensor[:, 1, ...],
            joint_state=self._env.joint_state,
            wrist_camera_pose_l=self._cam.camera_pose_l,
            wrist_camera_pose_r=self._cam.camera_pose_r,
            gripper_geometry_l=self._env.gripper_geometry_l,
            gripper_geometry_r=self._env.gripper_geometry_r,
            routing_target_seg_idx=routing_state.target_seg_idx,
            routing_target_clip_idx=routing_state.target_clip_idx,
            previous_estimate=previous_estimate,
        )


# thread_isaac_lab/estimators/core/__init__.py
# (MUST NOT import newton, env, or WristCameraManager)

from .pose_estimator_core import PoseEstimatorCore  # exports only core
# NO: from thread_isaac_lab.envs.wrist_camera_manager import ...  (forbidden)


# thread_isaac_lab/estimators/core/pose_estimator_core.py

class PoseEstimatorCore:
    """Pure tensor-in / tensor-out estimator. No env / sim dependencies."""

    def __init__(self, stage1_model, stage3a_solver, stage3b_solver, stage4_gate):
        self._stage1 = stage1_model
        self._stage3a = stage3a_solver
        self._stage3b = stage3b_solver
        self._stage4 = stage4_gate

    @enforce_input_boundary   # from v3.1 Appendix D
    def forward(self, inputs: EstimatorInputs) -> tuple[PoseEstimate14D, RegimeState]:
        stage0_out = self._stage0(inputs)
        masks = self._stage1(inputs.rgb_l, inputs.rgb_r, stage0_out)
        point_cloud = self._stage2_project(inputs.depth_l, inputs.depth_r, masks)
        cable_state = self._stage3a(point_cloud, inputs.previous_estimate)
        clip_state = self._stage3b(point_cloud, inputs.routing_target_clip_idx)
        regime, pose_14d = self._stage4(
            cable_state, clip_state, inputs.previous_estimate
        )
        return pose_14d, regime
```

### H.5 Why this boundary matters

1. **Testability**: `PoseEstimatorCore.forward` can be unit-tested with pre-recorded `EstimatorInputs` samples; no need to spin up full env + camera pipeline.
2. **Refactor isolation**: changes to `WristCameraManager` (e.g., scipy→Warp kernel migration per v3.1 CC3-4) do not propagate to core.
3. **Sim-to-real transfer**: in real deployment, `PoseEstimatorInputAdapter` is replaced with a real-hardware equivalent (RealSense driver + robot joint state reader); `PoseEstimatorCore` is reused unchanged.
4. **R6 enforcement**: the import lint test (§H.3) makes R6 input-boundary violation detectable at CI time, not runtime.

---

## Appendix I: FAIL_CLOSED Training Loss Mask Storage (v3.2, new)

### I.1 Trigger

v3.1 §8 (P7) specified Option C for FAIL_CLOSED in training mode:

```text
Training mode Option C (RECOMMENDED for v3.1 MVP-3 initial):
    allow PREDICT_TEMPORAL for up to K frames (default K=20)
    if estimator recovers within K → continue normally
    if estimator still FAIL_CLOSED at K → terminate as estimator_failure
    transitions within PREDICT_TEMPORAL included in policy update (policy learns to cope)
    transitions at FAIL_CLOSED terminal step masked from policy loss (avoid biasing value)
```

v3.2 Item 5 answers the implementation feasibility by specifying storage requirements.

### I.2 Storage schema (required extension)

THREAD uses `rsl_rl.storage.RolloutStorage` for PPO trajectories. v3.2 requires adding a `policy_update_mask` field:

```python
# thread_isaac_lab/rl/rollout_storage_ext.py

@dataclass
class TransitionExt:
    # Existing RSL-RL fields (unchanged):
    observations: torch.Tensor           # [T, W, 50]  (v3.2 augmented obs)
    actions: torch.Tensor                # [T, W, 12]
    rewards: torch.Tensor                # [T, W]
    dones: torch.Tensor                  # [T, W] bool
    values: torch.Tensor                 # [T, W]
    log_probs: torch.Tensor              # [T, W]
    # New in v3.2:
    policy_update_mask: torch.Tensor     # [T, W] bool
        # True: transition enters policy loss and GAE
        # False: transition excluded from policy loss (but GAE still uses value target for bootstrapping)
    regime: torch.Tensor                 # [T, W] int8 (0..3) for diagnostic logging
```

Storage cost: 1 bool tensor + 1 int8 tensor per transition = ~2 bytes × T × W. At T=24, W=32 rollout: ~1.5 KB per rollout (negligible).

### I.3 PPO loss with mask (implementation)

```python
def ppo_loss_masked(storage: TransitionExt, policy, clip_eps, **kwargs):
    """PPO loss with policy_update_mask support (v3.2)."""

    # Forward pass on all transitions (for value bootstrap consistency)
    new_values, new_log_probs = policy.forward(storage.observations, storage.actions)

    # GAE computed on ALL transitions (mask does NOT interrupt temporal credit)
    # Critical: if we exclude FAIL_CLOSED transitions from GAE, the earlier transitions'
    # advantage estimates become biased (missing value bootstrap).
    advantages = compute_gae(
        rewards=storage.rewards,
        values=storage.values,
        dones=storage.dones,
        gamma=kwargs["gamma"],
        lam=kwargs["lam"],
    )  # [T, W]

    # Policy loss: MASKED
    ratio = (new_log_probs - storage.log_probs).exp()
    clipped = torch.clamp(ratio, 1.0 - clip_eps, 1.0 + clip_eps)
    surr = torch.min(ratio * advantages, clipped * advantages)
    policy_loss = -(surr * storage.policy_update_mask.float()).sum() \
                / storage.policy_update_mask.float().sum().clamp(min=1)

    # Value loss: MASKED
    value_err = (new_values - storage.returns).pow(2)
    value_loss = (value_err * storage.policy_update_mask.float()).sum() \
               / storage.policy_update_mask.float().sum().clamp(min=1)

    # Entropy: unmasked (exploration signal over full rollout)
    entropy_loss = -policy.entropy(storage.observations).mean()

    return policy_loss + kwargs["value_coef"] * value_loss + kwargs["entropy_coef"] * entropy_loss
```

### I.4 Mask population (env-side)

```python
# In env's step():

def step(self, actions):
    ...
    for w in range(self._world_count):
        if regime_state[w] == RegimeState.FAIL_CLOSED:
            policy_update_mask[w] = False
            # PREDICT_TEMPORAL inside K-window: mask = True (policy learns to cope)
        elif regime_state[w] == RegimeState.PREDICT_TEMPORAL:
            policy_update_mask[w] = True  # policy learns to cope (Option C intent)
        else:
            policy_update_mask[w] = True
    ...
    extras["policy_update_mask"] = policy_update_mask
    extras["regime"] = regime_state.state  # int8
```

### I.5 Impact on GAE — critical correctness

Naively excluding masked transitions from GAE breaks temporal credit assignment. Correct handling (v3.2):

- **Include all transitions in GAE** (reward sum + bootstrap)
- **Exclude masked transitions from loss only**

This means the masked transition's value target still serves as bootstrap for its predecessor's advantage, but its own policy / value loss contribution is zero. Policy does NOT learn to predict the masked transition's action, but the value function remains consistent.

### I.6 Diagnostics output requirement

Log per-rollout:

```text
estimator_failure_rate     = mean(regime == FAIL_CLOSED)
predict_temporal_rate      = mean(regime == PREDICT_TEMPORAL)
predict_temporal_duration  = mean consecutive length of PREDICT
terminal_estimator_failure = mean(dones & policy_update_mask == False)
masked_transition_fraction = mean(~policy_update_mask)
```

Gate at MVP-3:

- `estimator_failure_rate < 10%` (v3.1 P7 gate)
- `predict_temporal_duration < 5 frames` mean (healthy estimator)
- `masked_transition_fraction < 15%` (policy loss computed on majority of transitions)

### I.7 Feasibility summary

| Concern | v3.2 answer |
| --- | --- |
| Is mask implementable in RSL-RL storage? | Yes — bool tensor field, ~20 LOC extension |
| Is GAE correct under mask? | Yes — mask the LOSS, NOT the GAE |
| Does this change PPO algorithm? | No — standard PPO with per-transition weight |
| Can it rollback if unstable? | Yes — set mask = all True = standard PPO |
| MVP-3 impl effort | ~2 days (storage ext + loss patch + unit test + integration test) |

**Verdict: implementable as specified, no algorithm-level risk.**

---

## 6. Revision history (v3.2)

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| v1 | 2026-04-25 06:00 | CC#4 | Initial proposal |
| v2 | 2026-04-25 06:55 | Rs (improved from v1) | Execution-oriented restructure |
| v3 | 2026-04-25 07:10 | CC#4 (post-debate) | 5-CC Debate revision |
| v3.1 | 2026-04-25 07:30 | CC#4 (Rs 12-point feedback patch) | 5 essential + 7 supporting |
| v3.1 §15 addendum | 2026-04-25 07:45 | CC#4 ("継続") | Env verification, 42D→45D / 47D→50D correction |
| **v3.2** | **2026-04-25 07:55** | **CC#4 (Rs minimum patch)** | **5 items: arithmetic consolidation, Appendix E 45→50, epsilon-var forbidden, module boundary (Appendix H), FAIL_CLOSED storage (Appendix I)** |

---

## 7. Summary (v3.2)

v3.2 is a minimum patch completing v3.1:

- **Item 1+2+3 consolidated**: all 42D/47D residuals replaced with 45D/50D; Appendix E fully rewritten; normalizer epsilon-variance forbidden (regime+conf dims use raw pass-through, not normalized) — preserves initial bit-identical behavior under augmented obs contract
- **Item 4 (Appendix H)**: `PoseEstimatorInputAdapter` / `PoseEstimatorCore` module boundary made explicit with import-lint test for R6 enforcement; core module has no env / newton / WristCameraManager dependencies
- **Item 5 (Appendix I)**: FAIL_CLOSED training loss mask specified as `policy_update_mask: Bool[T, W]` field in `RolloutStorage` extension; GAE uses all transitions, loss masks FAIL_CLOSED only; feasibility: ~2 days MVP-3 impl effort

Algorithm / design direction unchanged from v3. Only arithmetic, module layering, and storage schema specified.

Next action: Rs approval on 9 pending OQs (OQ-1a / OQ-1b / OQ-2 / OQ-3 / OQ-4 / OQ-5a / OQ-5b / OQ-5c / OQ-6). v3.2 does not introduce new OQs.

---

## Cross-references

- v1 (superseded): `thread-vault/07-Design/PoseEstimation-Design-v1.md`
- v2 (Rs X2 stock): `thread-vault/07-Design/PoseEstimation-Design-v2.md`
- v3 (post-debate parent): `thread-vault/07-Design/PoseEstimation-Design-v3.md`
- v3.1 (12-point patch + §15 addendum): `thread-vault/07-Design/PoseEstimation-Design-v3.1.md`
- **v3.2 (this minimum patch)**: `thread-vault/07-Design/PoseEstimation-Design-v3.2.md`
- Downloads: all versions mirrored
- Memory pointers: `project_pose_estimation_design_v{1,3,3_1}.md`; v3.2 pointer to be added
- Handoff: `memory/handoff_cc4_pose_estimation.md`
