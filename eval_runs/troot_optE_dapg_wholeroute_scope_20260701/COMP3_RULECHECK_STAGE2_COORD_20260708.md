# /rule-check stage2 — comp3+comp4 (plan v2) Tier 0-3 checklist — %11 COORD

**node:** T-ROOT-optE-route-dapg-C1C2-P2-routeexec — comp3 Stage-B, [RULE-CHECK] before [CHANGE].
**planned change (L3):** comp3+comp4 per plan v2 (`653a8c967b`) — grasp_actuation flag-flip (newton_route_env.py:391, flag-gated) + write-site flag-gate (:440/:791 arm-only flag-ON; :670 AR-precedent reset) + grip staircase replay via a RouteExecutor accessor reusing `_set_gripper_target` (route_executor.py:967) + guards (flag-matrix / discriminating servo readback / .assign() device-robust / _settled_fk_jq patch / env-owned index maps) + obs[7]/[15] flag-ON physics readback.
**code file set (build constraint, %12):** {newton_route_env.py, route_executor.py} ONLY (zero drift into task_config.py / newton_skill_env_base.py / locked test file). **validation artifacts:** test_routeexec_state_bank.py (extend, existing) + comp3_void_readback.py (new no-GPU probe, plan §15-enumerated + %12 re-gate approved).

---

## Tier 0: prohibited.md 照合 (fresh cat, 40 lines)
- ✅ **Read:** `cat .claude/rules/prohibited.md` = 40 lines.
- ✅ **照合 L19-23 (PhysX control API: `write_joint_position_to_sim` 全面禁止 / `write_joint_state_to_sim` 制御ループ中禁止 [例外: reset直後初期化 episode開始時1回 許可] / finger `set_joint_velocity_target` のみ):** **PhysX-SCOPED (L19 explicit「以下はPhysX制御API制限。Newton環境は LL-Newton.md 参照」), route env = NEWTON ⇒ N/A.** Evidence: `grep -c write_joint_position_to_sim|write_joint_state_to_sim` on both files = **0**. The Newton route env uses `joint_q.assign()` / `control.joint_target_pos.assign()` (warp arrays) = the Newton pattern; the gripper is a POSITION servo (base grasp_actuation), NOT PhysX velocity-only. The :670 28-wide reset-init `.assign()` = the sanctioned reset-init (episode-start-once, analog of L22 exception).
- ✅ **照合 L26 (kinematic attachment/trick 禁止):** comp3 RESPECTS. gripper closes by PHYSICAL POSITION servo (grasp_actuation restores the actuated 4-bar); comp4 EXCLUDES gripper coords {6-13,20-27} from the kinematic joint_q write (route_executor.py:20-24/80 `_GRIPPER_COORDS_LOCAL`; "left to the servo"). /pre-check verified no-kinematic-trick RESPECTED. NOT a teleport/forced-placement.
- ✅ **照合 L39 (PhysX/Newton 混同禁止):** comp3 applies ONLY Newton conventions (mujoco POSITION-drive servo, joint_q.assign); force-design explicitly scoped the PhysX velocity-only rule OUT. No PhysX rule applied to Newton or vice-versa.
- ✅ **照合 (CLAUDE hard-stop 新ファイル/新Phase/新CLI 無断作成禁止):** code file set = 2 EXISTING files; the 2 validation artifacts (comp3_void_readback.py + test extension) are plan §15-enumerated + %12 re-gate-approved (not unsanctioned). No new Phase/Gate/CLI arg.
- **Tier 0 = PASS** (no applicable prohibition violated).

## Tier 1: Hard Stops
- ✅ Same error 3× without success? NO — v2 = clean fold of the 5体 verdict; first comp3 build.
- ✅ Prohibited API/trick "just this once"? NO.
- ✅ Patch-of-patch chain? NO — v2 is a verdict-driven redesign (R1-R8), not a patch chain.
- ✅ "Works but root cause unknown"? NO — root cause = env-core builds fingers-pinned-OPEN (inert grip, verified :779/:791); comp3 activates the servo + comp4 excludes gripper from kinematic write.
- ✅ Impact scope statable? YES — {newton_route_env.py (:391 flag / :440,:670,:791 write-sites / obs[7],[15] / guards / index maps), route_executor.py (grip accessor)} + test artifacts. flag-OFF = byte-preserve; flag-ON = live grip.
- ✅ Editing a file not cat'd this session? Key sections READ (newton_route_env.py :252-421/:729-800, route_executor.py :80-305/:891-978, base gates :1484-1600/:1738/:1905). ⚠ **§運用16 build-time requirement: fresh-cat EACH file immediately before EACH edit** (this is PRE-change; build not started).
- **Tier 1 = PASS.**

## Tier 2: Change-Specific
**Control API (touching gripper control — Newton):**
- ✅ DifferentialIKController for IK? comp3 does NOT change the arm IK (`_solve_ik_batch` unchanged); N/A to the grip change.
- ✅ No write_joint_position_to_sim / write_joint_state_to_sim (control loop)? grep=0 (PhysX APIs; Newton assign pattern). :670 reset-init = episode-start-once (sanctioned).
- ✅ No kinematic attachment/trick? gripper physical servo close; comp4 exclusion (Tier 0 L26).
**Params (comp3 changes NO params):**
- ✅ SSOT maintained? task_config.py UNCHANGED (zero drift); grasp_actuation gates pre-exist in base:1537/1586/1738/1905; the env only passes the kwarg :391.
- ✅ Ground-truth for new values? no new metrics; discriminating servo readback asserts ke==66.7/kd==2.0/effort==2.5 (ground-truth from task_config:314-316); force/geometric/reward-design done.
- ✅-note Values consistent with SOMA? LEDGER (成否SSOT :47) current + consistent. ⚠ SOMA carries no route-executor row (known planning-surface gap — PLAN-KEEPER/%12 charter surface, NOT comp3's to fix; logged 04e05a8066).
**Files (all changes):**
- ✅ cat'd target files this session? YES (above). ⚠ fresh-cat before EACH build edit (§運用16).
- ✅ grep'd reference locations? YES (write-sites :440/:670/:791; `_set_gripper_target` call sites :1031/1567/1573/2051/2071/2091/2418; `_GRIPPER_COORDS_LOCAL`).
- ✅ Will grep old values after change? YES — post-build: flag-OFF byte-identity (static diff) + no missed gripper write + servo readback.
- ✅ No new file without Rs confirmation? validation artifacts plan §15-enumerated + %12 re-gate-approved.
- **Tier 2 = PASS.**

## Tier 3: Workflow Compliance
- ✅ Vault refs checked/reported? §運用4 grounding: LEDGER:47 / node state.md / plan v2 / 5体 verdict / base+route+executor code / SRG. (reported across comp3 pings.)
- ✅ Relevant skills loaded + protocol output? /force-design + /geometric-design + /reward-design + /pre-check ALL run with committed outputs (design-gate + gates 2/3); this /rule-check stage2.
- ✅ Evidence for each step? commit chain d718acc7f8 → 4394525821 → c80a546f6c (verdict) → 42cff7b0c4 (v2) → de49c2dedd → 653a8c967b (3 gates) → this.
- ✅ [VERIFY] adversarial documented? 5体 [VERIFY] DECIDE=REVISE (all R1-R8 folded, no rebut) + /pre-check skeptical sub-agent PASS.
- **Tier 3 = PASS.**

## %12 build constraints (re-stated, all encoded in plan v2)
- ✅ file set = {newton_route_env.py, route_executor.py} only (Tier 0 / plan §15).
- ✅ route_executor.py edit → byte-repro ref-leg self-check re-run (NHA cond5, plan §16) — WILL run.
- ✅ G1 world_count=1 pin (ISSUE2, plan §13) — G1 is GPU-deferred anyway.
- ✅ flag-OFF byte-exact = static diff + CPU write-pattern unit BEFORE flag-ON legs (plan §12/R5).
- ✅ no-GPU legs ONLY (L1/L2/L3/L4); GPU G1 = Rs surface.
- ✅ post-build = §運用15 層3 → %12 verify → 層2 post-debate → 層5.

## RESULT: ALL PASS (Tier 0-3 + %12 build constraints)
No ❌ FAIL, no ⬜ undecided. ⚠ carried build-time requirement: §運用16 fresh-cat before each edit; §運用4 SOMA gap is a separate PLAN-KEEPER surface (not comp3).
→ /rule-check stage2 = PASS → (per %12 conditional pre-auth) BUILD may START on the no-GPU legs, honoring the constraints above; any FAIL/undecided mid-build → STOP + ping.

---
*%11 COORD (w2:p3) 2026-07-10. /rule-check stage2, planned change = comp3+comp4 plan v2. ALL PASS. → %12 sha ping (conditional build pre-auth).*

> **2026-07-10 supersession (5tai verdict a35cb359a0 / fix 65b5b9dd21 + folds):** the flag-OFF (lines 22/38/53) byte-identity/byte-preserve claim is SUPERSEDED at the EE-Z floor clip site (newton_route_env.py, _apply_actions_batch target z clamp) — the lane-aware floor (Rs adjudication B) is an env-core latent-defect fix common to BOTH flags: flag-OFF close-window + descend targets change by <=3.12mm (achieved-col window start {896..900}, target-col from {859..863}). All other flag-OFF surfaces remain byte-preserved.
