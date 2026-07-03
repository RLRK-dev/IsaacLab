# DQ7 stage-(ii) — Rs GO (band=γ + injectable-only + GPU-recording 承認)

**Timestamp:** 2026-07-03 12:11 JST
**Recorded by:** %12 RS-TECH-LEAD (recording Rs decision; design = Rs 専権)
**Node:** T-ROOT-optE-route-dapg-C1C2 / DQ7 stage-(ii)
**Resolves:** the 2 Rs-carry decisions (band, gate-reachability) + the GPU-recording loud-notify gate — all three now CLOSED.

## Rs verbatim
「γ、injectable のみ GO で承認 進めて」 (2026-07-03 ~12:11 JST; %11 pane relay / Rs direct)

## 3 decisions + effects

### ① band 再較正 = γ  (charter §7 / mini-spec §7)
- γ = per-axis OG band: **X,Z gain ∈ [0.7,1.3] AND Y gain ≤ 0.3 AND ee-only ≤ 0.3**.
- Why γ (not α/β): faithful expert pair seg-follow = per-axis (X:1, Y:0 [88mm HOLD], Z:1) → 3-axis mean ≈ 0.667 < old band-lo 0.8 (U4, code-verified). **α** [0.8,1.2] would STOP a faithful expert (known-miscalibration); **β** mean-band is coarse; **γ** is physics-faithful (Y = 88mm-span HOLD is legitimately non-following). %9 confirmed γ physically correct.
- **Effect:** at **CP-(ii)-5 (OG gate) ONLY**, the OG instrument gets an ADDITIVE per-axis band + regression (old mean printed alongside). Does NOT affect recording/training. Was a CP-(ii)-5 blocker → now UNBLOCKED.

### ② gate-reachability = injectable-only GO  (mini-spec §H.1/§I; %9 Rs-carry)
- The GO verdict keys on the load-bearing INJECTED cells **{1}(GRASP_DESCEND), {11}(C2_REGRASP R)** via the §H directional-γ⊥ check (did their γ⊥ move ↓ toward the restoring bar). This is the kick-and-recover mechanism verdict.
- {2}CLOSE / {3}LIFT = un-injectable (choreography-sensitive), {0} = single-call generalization-only, {4,5,10,12,13} = v3 fills. A full-movable-{0-3}≤0.5 STOP at {2,3}/{0} is EXPLICITLY attributed to **un-injectability** (no v1 teacher by scope) — NOT a kick-and-recover mechanism failure, and MUST NOT be read as "(ii) が (iv) 同様に失敗" (distinct from (iv)'s synthetic-obs model-consistency failure).
- **Effect:** CP-(ii)-5 verdict template pins injected-cell {1},{11} γ⊥ movement = the mechanism verdict; un-injected {2,3}/{0} γ⊥ static = expected-by-scope (informative, not GO-blocking). Was a CP-(ii)-5 blocker → now UNBLOCKED.

### ③ GPU-recording GO = 承認 進めて
- **two-key** fully satisfied: (iv)-A key replaced by Rs direct GO (08:3x「推奨で良い」→ Option A adoption) + **%9 concur** (`DQ7_STAGE_II_V2_REVALIDATE_PCT9.md`, v2 PASS). loud-notify gate (§K locked-file disclosure + 条件3: GPU-h ~3-5h / device pins / (iv) 数値 / wave 粒度 early-abort / 中断手順) presented → Rs answered GO.
- **HIGH-COST-GATE = 非該当** (adjudged at D-1..D-5 stage, %9 confirmed — ~3-5 GPU-h, non-production-RL recording, gated by two-key + loud-notify + wave-1 abort). `/production-launch-gate` NOT required.
- **Effect:** **CP-(ii)-1 build UNLOCKED.** Proceed per charter §8 + mini-spec §K chain.

## Build authorization (CP-(ii)-1, executed by %11)
- Build hooks (flag-gated `PERTURB_INJECT`, default-off) + converter outbound-mask branch + recorder meta, per `dq7_ii_mini_spec_v2.md` (**kick-and-recover; dwell ABOLISHED** — v1's hold-at-offset was killed by L3 CRIT U2).
- **Build-review binding (C1/C2, non-design, %9-corrected):**
  - **C1 (VERDICT-CRITICAL):** converter KEEP/DROP + regression assert key on the **COMMANDED target (offset==0 = released) / `injection_windows` membership, NOT achieved-ee_pos**. A recovery frame's achieved ee_pos is legitimately off-path (script+offset→script transit); an achieved-keyed assert would DROP the restoring teachers → validity passes but γ⊥ static = a **FALSE Outcome-B**. Do NOT assert `achieved ≈ script`.
  - **C2:** affine p2r box tol = recovery excursion (≈offset ≤20mm) allowed + **expand-not-clip** (amax ≤ 0.95). Per-phase affine ⇒ only {1}/{11} boxes expand.
- **Locked-file (L3):** `test_newton_clip_routing.py` markers [4401,4417,4516] untouched; {11}=:4481 RHOVER only + regrasp_ok guard; None-path byte-identity (**2-leg/2-sha**, baseline sha e01ac1fa…).
- **Staged abort:** wave-1 = 4 recordings ({0,1}inj×2 / {11}inj×1 / adj-A×1) → validity + span-watch (INV#2, >5mm span逸脱 = invalid-mark) + §運用14 video legs (skill-path: /video-analyzer or video-analyst; injection→release→recovery 視認 + 把持 phase claw-zoom slip/drop 検査) → %12 loud wave gate → 残 batch. Early-abort = wave-granular.
- **Devices:** recording cuda:0 / MUJOCO_GL=egl + DISPLAY unset / GPU-0 4-way ≤4 proc; training GPU-1.
- **0-commit** during build; commit judgement = %12.
- **rollout PROHIBITED** (OG GO 後も別途 Rs GO; standing 禁止不変).

## Gates satisfied (audit trail)
| gate | status | evidence |
|---|---|---|
| two-key | ✅ | Rs direct GO (key1) + %9 v2 CONCUR (key2, `DQ7_STAGE_II_V2_REVALIDATE_PCT9.md`) |
| loud-notify | ✅ | presented (§K + 条件3) + Rs answered GO |
| HIGH-COST-GATE | ✅ 非該当 | D-1..D-5 %9 adjudication (`DQ7_CONSULT_PCT9_VERDICT.md` O-1) |
| L3 pre-debate | ✅ | v1 FAIL (3 CRIT+7 HIGH) → v2 kick-and-recover → conformance PASS → %9 re-validate CONCUR |
| band (CP-(ii)-5 blocker) | ✅ DECIDED | γ |
| gate-reachability (CP-(ii)-5 blocker) | ✅ DECIDED | injectable-only |

— %12 RS-TECH-LEAD 2026-07-03 12:11 JST
