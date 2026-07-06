# P2 部品② route-executor — BUILD 計画 (COORD %11 起草, %12 checkpoint 用) — 2026-07-07

**node:** `T-ROOT-optE-route-dapg-C1C2-P2-routeexec` (state.md 済, IN_PROGRESS, 1:1 bind %11/w2:p3) · **L:** L3 (charter §3 自動昇格 confirmed, §1 で再導出 concur)
**charter-giver:** %12 RS-TECH-LEAD (w2:p4) · **task-start SHA:** `f0bd54992c` (5体 [VERIFY] git diff 起点)
**status:** PAPER-ONLY / 0-build / 0-commit-of-code (本 doc = charter INPUT、[DESIGN-GATE]+5体 [VERIFY] への提出物)
**rev:** v1.1 (%12 checkpoint 00:32: fn-range 3692-7475 / canonical 抽出 3692-5765 [§運用10 catch] / 27-closure 3-way / namesake / 6 coarse G) → **v1.2 (%12 design-gate BLOCK disposition 01:22 `dfe5dd0920`: /pre-check 2 CRIT fold — DoD 2-layer 分離 [Layer A 抽出忠実 primary verdict+trajectory / Layer B substrate-transfer 実測] + gripper-servo env-core drive-loop 拡張 [Q2] + HIGH4 no-global-mutation + MED5 INIT_XY_NOISE=0 + MED6 reset_to_phase per-world)** → **v1.3 (re-pre-check BLOCK fold: CRIT1 自前 IK stack verbatim copy 確定 [1-ULP monkeypatch → import-reuse 撤回] + Issue2-7 fold [execution-model / env-core ⑨a′ 再regression / citation :724-727 / reset cable-state / bank-vs-monolith spot-check])** → **v1.4 (5体 [VERIFY] FAIL fold — governance-independent GO %12 02:29: CRIT1 capture + CRIT2 L∞→ee_tgt HARD/joint_q tol-band/self-repro + CRIT4 reset FULL per-world+1-step + MED5-8,10-12; **env-source CRIT3/MED9 = ⭐Rs 決定 A `bad0d25204` で fold [cross-node 3 箇所 servo/C2-clip/route-swap 全 default-off + legacy-config ⑨a′ 保全]** + /force-design skip)** → **v1.6 (servo-scope escalation DISPOSITION Rs=A `9b9a41604c`, %12 disposition 05:17 / plan-ACK 05:23: full 5体#2 FAIL fold — v1.5 drive-loop servo [駆動 actuator 無く inert] 撤去 → `grasp_actuation=True` flag-flip [proven base:1586-1740 build_scene mirror, route:339 kwarg default-off = env-core COMPLETE `grasp_actuation=False` 認定 byte-preserve, 4th flag] + full 5体#2 HIGH/MED 10項 + %12 sequencing [Layer A byte-repro front-load, Layer B 独立 cycle] + design-gate /geometric-design table-void 新 pass 必須。⭐§10.1 が v1.6 grip 機構 governs — §2(b)/§9 の v1.5 servo drive-loop 記述は SUPERSEDED [historical])**

---

## §0. Grounding report (anchor set, §運用4 hard gate — read + cite 済)

| Anchor | Cite (file:line) | 使用 fact |
|---|---|---|
| 成否 SSOT | `00-DESIGN-STATUS-LEDGER.md:47` (LADDER v2 行, `e48facd37d`) | env-core COMPLETE / staged chain (env-core→**route-executor**→oracle→OG→trainer) / route-executor = 第2 component |
| charter [DEFINE] | `ROUTE_EXECUTOR_CHARTER_SCOPING_RSTECHLEAD_20260706.md` §1/§4/§5/§6 | goal/means/success + scope partition (8 carry のうち 7+⑬enabler owns) + stub 契約 v1 + **D-1=C / D-2=trainer (Rs 23:5x)** |
| node spec | route-executor `state.md:5-16` (goal_verification DoD ①-⑧) | DoD 定義 (byte-repro 全項前提) |
| banked spec | `P2_ROUTE_ENV_SPEC_INPUT_W0C` v1.5h §2-F2(line29) / §5(77) / §7:102 | state-bank fork (b) precomputed phase-k / oracle=別stage / route-executor 抽出 = 300-800 touched |
| env-core build plan | `BUILD_PLAN_ENVCORE_COORD_20260706.md` §6(40-50 stub 契約 v1) / §12(143 CC5-2) | reset_to_phase / step_target→(target_6d,phase_id,grip_cmd) / per-arm grip 2-vec / is_dual_grip boolean / recorded-target-replay |
| 8 blocking carry | env-core `state.md:62-71` (COMPLETE 節) | route-executor が discharge する 8 項の正式列挙 |
| locked runner 実体 | `test_newton_clip_routing.py:3692` `_run_mujoco_grasp_route` (**fn body 3692-7475 ~3784L**; 次 top-level def `_run_mujoco_episode`:7478 で確定) | ⛔ ANTI-REVERT Rs-LOCKED (marker :5128/:5148/:5290) = 0.716 MOTION STANDARD source = **reference oracle (不触)** |
| **canonical 抽出域** | `_run_mujoco_grasp_route` 内 **3692-5765** (`if _ROUTE_C2 and _clip_collidable:`:4375 → `sys.exit`:5765) | 0.716 byte-repro を決める唯一の path (route_c2_pin.json dump:5758 / demo finalize:5763 ≤5765)。**5766-7477 = dead-under-canonical** (下記 §2) |
| 抽出先 interface | `newton_route_env.py:178` `NominalRouteStub(rc.RouteInterfaceV1)` + `:309`/`:1101`/`:1120` | env-core が既に呼ぶ stub = route-executor が実装で差し替える integration point |
| shared IK helper | `test_newton_clip_routing.py:1958` `def ik_move_both` | route の move primitive (monolith 内部でない)。⚠ **v1.3: monkeypatch 1-ULP ゆえ import-reuse 不可 → 自前 copy** (§2 IK stack / §9) |
| goal 上位 | `SOMA.md:37` (100% qualitative) / `:717` (L2 「No T-ROOT 95% claim」) | route-executor は route engine、**SR/学習成果 claim を出さない** (trainer/campaign) |
| provenance | `w0e_81rerun_snapdown_0537/` (cell_x*_y*) + `route_demo_recorder.py` | FON_V1 (W0E_F1B_SNAPDOWN=1) 0.716 canonical recorded targets / recorded-target-replay source |

**grounding 由来宣言:** 上記は全て **session 内で cat/grep 実読** (handoff narrative / memory を ground truth にしていない、§運用4)。locked runner は fn 全域 (3692-7475) を構造 grep + **top-level 分岐 reachability を canonical env-gate で検証** (w0e_81rerun_snapdown_runner.sh 実読) + canonical 抽出域 (3692-5765) の phase/predicate 区間を実読。

---

## §1. [TASK] / [L-TRIAGE] confirm

### [TASK] — node (charter §2、%12 作成済)
- node `T-ROOT-optE-route-dapg-C1C2-P2-routeexec` (parent = `T-ROOT-optE-route-dapg-C1C2`、env-core sibling)。state.md 作成済 (IN_PROGRESS)、parent `children_nodes` 追加済 (p6 反映)。1:1 bind builder = %11 (再 bind)。

### [L-TRIAGE] = **L3** (charter §3 と独立に再導出、concur)
| 判定軸 | 証拠 | 結果 |
|---|---|---|
| path/keyword | 抽出対象 `_run_mujoco_grasp_route` = newton/mujoco/ik/solver/physics + `_ph`(phase) state-bank + G1-G6 success predicate live | §0 L3 diff-keyword 該当 |
| 規模 | 新 route module (~500-800L) + byte-repro harness + C2 scene + env 統合 → >200 行 / ≥3 file | L3 定量該当 |
| **FOUNDATIONAL INVARIANT (最優先)** | 本 node は §0 不変前提 (DUAL-ARM / 88mm span / DiffIK-only / コ gripper / no-kinematic-trick) を**変更しない** — faithful 抽出は挙動不変が前提、**byte-repro が invariant 保存を構造 enforce** (RS71 §0 #1-5 は monolith が既に満たす) | **即 STOP 非該当**。ただし Rs-LOCKED code 関与ゆえ **high-care L3** |
| gate 帰結 | design-gate (直交) + 5体 [VERIFY] (L2以上) + 層5 (L3) + 事後 debate (L3) | env-core と同型 chain |

**⚠ high-care 注記:** 本 node は §0 不変前提を変えないが、**0.716 MOTION STANDARD (Rs-LOCKED) の faithful 抽出**ゆえ、通常 L3 より先祖返り risk が高い。一次 guard = byte-repro regression (§4)。抽出中に「挙動を変える」判断が必要になった場合は **STOP → BLOCKED_FOR_USER (Rs)** — 抽出は挙動 delta ゼロが契約。

---

## §2. scope (抽出アーキテクチャ + component/LOC) — 新規 module + byte-repro guard

**D-1=C 帰結 (Rs 23:5x):** locked `_run_mujoco_grasp_route` (reference oracle) **不触**、canonical route ロジックを新 `route_executor` module (production engine) へ faithful 抽出。両者の **byte-repro regression (cuda:0 canonical strict_v2 58/81 EXACT) = 全 DoD 前提 + 先祖返り guard**。

**⚠ 抽出 scope = canonical path のみ (3692-5765、%12 CONCUR 00:32 `16574fa4bb`):** fn body は 3692-7475 だが、canonical 0.716 gate (`S13_ROUTE_C2=1` + `CLIP_COLLISION=1`; `STEP13_REGRASP`/`CLIP_DELTAH`/`S6_HOOK` OFF) 下では `if _ROUTE_C2 and _clip_collidable:`:4375 block が **`sys.exit`:5765 で終端** (fn-body exit は 5765 単一; 4375-5765 の他 return は全て nested closure 内)。⇒ **5766-7477 (`DO_HOOK`:5775 [= `(S6_HOOK==1) and not _ROUTE_C2` = False] / `STEP13_REGRASP` block:5921 / `CLIP_DELTAH` block:6080 + `_b` closures) は canonical 下で全 dead = reference-oracle-only variant** (抽出/byte-repro scope 外)。byte-repro (strict_v2 58/81) は完全に ≤5765 で決定 (route_c2_pin.json dump:5758 / demo finalize:5763)。将来 C2 re-grasp variant が要れば locked oracle (full fn 保持) を参照。**これは under-scope 修正でなく over-scope 回避** — 抽出は clean で小さい (dead ~1712L を抽出しない)。

**SSOT 規律 pin (env-core §1 継承):** 新 config param = 新規 route-executor 専用のみ。`task_config.py` / `route_env_config.py` の既存値は **import 参照のみ・複製禁止**。**locked runner 不触 / task_config.py 不触。**

**抽出単位 (charter §5):** canonical 2073L (3692-5765) → per-step **`step_target(t)`** (target-computation) + phase-k **`reset_to_phase(k)`** (state-bank driver)。canonical 内訳を **抽出 / harness残置 / dead** で 3 分類 (silent drop 禁止):

| canonical 部位 (≤5765) | 分類 | 行き先 |
|---|---|---|
| phase state machine (`_ph`:3761→C2_SETTLE:5451 の 15 label = 遷移構造) + inline per-step target (seat k/8 補間 + ANTI-REVERT argmin/square-on/regrasp :5128/:5148/:5290) | ✅ **抽出** | `step_target(t)` phase 別 generator |
| **target/IK closures 7個**: `tgt`:4197 / `tgt2`:4200 / `_w0e_guarded_cx`:4205 (F-1a comp) / `_rot_quat_rx`:5156 / `_cable_local_pitch`:5161 / `_solve_ik_dual_rot`:5171 (square-on C2) / `_clip2_geoms`:3859 (C2 scene) | ✅ **抽出** | `RouteExecutor` method 化 (fn-local closure → `self` に state 保持で method 化 = closure import 不可の解、%12 finding(3) 反映) |
| grip schedule (2-phase close / L_HALF_UNCLAMP:4735 / C2_REGRASP:5145) + is_dual window | ✅ **抽出** | grip scheduler (base single-source, CC5-2) |
| phase-k qpos/qvel snapshot | ✅ **新規** (monolith に無) | `reset_to_phase(k)` (**6 coarse G**, §5) |
| **measurement closures 15個**: `_min_dist_mm`:3837 / `_cage`:3895 / `_seg_z_mm`:3928 / `_zc1`:4662 / `_claw_cable_load`:4431 / `_claw_table_load`:4448 / `_claw_c2_load`:4461 / `_sample`:4299 / `_arm_split`:3937 / `_cable_z`:3924 / `_hh_clear_mm`:4421 / `_f1_zmin_mm`:4476 / `_cage_pair`:3882 / `_clip_geoms`:3845 / `_table_geoms`:3872 | ❌ **residual** | harness/env 残置 (predicate = env-core owns) |
| video `_cap`:4045 / `_world_to_pixel`:4024 + recorder `_ph`(label)/`_gn`:3802 + DR `_inject_detour`:3768 (None-passthrough) | ❌ **residual** | route engine 責務外 |
| **IK stack (v1.3 自前 copy 確定 / v1.4 cite 訂正)**: `ik_move_both`:1958 + `solve_ik_dual`**:1854** (v1.4 CC4-CH5: 旧 :1814 は 40行 drift) + `_solve_ik_dual_rot`:5171 + `_rot_quat_rx`:5156 (harness は def-grep で解決、hardcode line 禁止 = namesake guard) | ✅ **抽出 (verbatim copy → route_executor.py 内)** | ⚠ **v1.3 DECIDED (re-pre-check CRIT1)**: golden C2 re-grasp は monkeypatch `_solve_ik_dual_rot` 使用、tilt=0 でも `_rot_quat_rx` sin/cos (=`sin(-π/4)`) は literal `solve_ik_dual` target (:1898) と **1 ULP 差 (実測)** → import-reuse ik_move_both (literal global 解決) では Layer A byte-identity **不能**。∴ IK stack を **自前 module に verbatim copy** し in-module 解決 (不触 file の global mutate せず = HIGH4 両立)。「explicit solver pass」= ik_move_both 署名 (:1961 solver=physics) 変更要ゆえ **不採用** (Issue2) |
| `_set_gripper_target` / `get_ee_positions` / geom helpers (module-level, IK 非依存) | ❌ **import 再利用** (不触) | 既存 module 参照 (global monkeypatch 非関与ゆえ reuse 可) |
| predicate (`c2_seated_honest`:5580 wall-excluded / `c1_final`:5586) | ❌ **env-core owns** (G6 strict_v2 mirror v1.5f) | reference oracle 側で byte-repro 照合 |
| **`_b` closures 24個 (≥5766)**: `_close_b`:6501 / `_halfclamp_b`:6511 (しごき) / `_feed_claw_cable_load_N`:6548 / `_gap_mm_from_drv`:6469 / `_span_sag_mm`:6589 / `_do_step_b`:6480 等 + DH-F1-R-DESCEND:6168 + STEP13_REGRASP/CLIP_DELTAH block | ⛔ **dead-under-canonical** | reference-oracle-only (抽出せず、loud 記録; %12 finding(3) の closure は dead 側) |

**closure 会計 (§運用28、%12「25」と当方「27」reconcile):** canonical ≤5765 = **27 closures** (exact grep `awk '/^ +def /' 3692-5765`)。うち **抽出 = 7** (target/IK) / **residual = 20** = measurement 15 + video 2 (`_world_to_pixel`/`_cap`) + recorder/naming 2 (`_ph`/`_gn`) + DR-passthrough 1 (`_inject_detour`) = 15+2+2+1 = 20 (7+20 = 27 ✓)。%12「25」との差 2 = **underscore-less `tgt`:4197 + `tgt2`:4200** (%12 grep `def _` が underscore 無 closure を取りこぼし = %12 own 00:47; 当方 grep `def ` は全 27 捕捉)。両者は EXTRACT 側 (target constructor)、分類は 7-extract に既計上で不変。dead ≥5766 = **24** (%12 一致)。⇒ **抽出対象 = 27 closure 中 7 のみ + inline orchestration** = LOC は canonical span より遥かに小。

**新規/変更 file (core module ≤800L、byte-repro test 分離):**
| file | 内容 | 行 (見込) | reuse |
|---|---|---|---|
| **新規** `thread_isaac_lab/envs/route_executor.py` | `class RouteExecutor(rc.RouteInterfaceV1)` = step_target/reset_to_phase(6 coarse G)/grip scheduler/recorded-replay mode。**抽出 = 7 closure (target/IK) + inline orchestration + IK stack 自前 copy (下記 manifest)**; geom/physics_step/get_ee_positions は import 再利用 | ~400-650 (+IK stack ~150-250) | canonical route-logic 抽出 + IK stack copy |
| **変更** `route_env_config.py` | C2 groove block (ROUTE_C2_XY / ROUTE_C2_GROOVE_Z) — 既存 ROUTE_* block (`a6cbc148ab`) に追加、meta verbatim+provenance | ~40-60 | env-core ROUTE_* pattern |
| **変更** `newton_route_env.py` (⭐Rs=A cross-node、全 default-off flag) | (a) `self._route` = `NominalRouteStub` → `RouteExecutor` 差し替え **default-off flag** (:309、off=stub 維持) + reset_to_phase per-world 実配線 (b) **⚠v1.6 SUPERSEDED→§10.1 — v1.5 drive-loop servo [駆動 actuator 無く inert] 撤去 → `grasp_actuation=True` flag-flip (build_multiworld_scene call:339 kwarg default-off、proven base:1586-1740 build_scene mirror、:738 kinematic write から全16 gripper coords 除外、route grip_cmd = drivers[6,10,20,24] joint_target_pos schedule)。以下 v1.5 記述は historical**: gripper-servo drive-loop 拡張 (default-off flag, ⚠v1.5 re-pre-check CRIT で機構訂正)**: env-core :738 は `phys_jq[jq0:jq0+_N_ARM_JOINTS(28)]` = **gripper DOF (6/10/20/24) 含む全 28-slice を kinematic 上書き** → 旧「pre-loop rewrite で :731-742 不編集」は **finger kinematic close = no-kinematic-trick 抵触ゆえ撤回**。**正 = servo-on 時、monolith `_ARM_OVERWRITE_IDX`:1776/:1827 (gripper coords 除外) pattern で :738 write を gripper-DOF 除外 + PD `control.joint_target_pos` schedule で dynamic close** (monolith :1826-1828 proven)。**servo-off = 全 28-slice 維持 = byte-identical** (default 保全)。∴ :731-742 は gated 編集 (off で byte-safe、CC5-CH4 の「不編集」は撤回) | ~40-80 + ~80-140 (servo+exclusion) | mujoco-コ position-drive `_set_gripper_target`:3019 (PhysX velocity-only 非適用) |
| **変更** scene builder (`newton_skill_env_base` C2 add、**`add_target_clip_c2` default-False flag**) | C2 target clip 建設 (env-core=C1 only:344, skill_base:1826 pattern)。base は既に add_target_clip flag-gate :1491 → 同 pattern で C2 flag、**default-off で grip/AR/AC scene byte-unchanged を grep-confirm (MED9)** | ~50-100 | C1 pattern mirror |
| **新規 (test)** `thread_isaac_lab/scripts/test_routeexec_byte_repro.py` | byte-repro regression harness (§4): locked oracle ↔ RouteExecutor 81-grid strict_v2 EXACT | ~150-250 | w0e_81rerun harness + test_route_geometry_sync pattern |

**⚠ LOC 見込 v1.2 (core ~400-650 + 変更 ~130-240 + **gripper-servo ~60-120** + test ~150-250 ≈ 740-1260 total):** canonical 2073L の大半 (20/27 closure) が harness-residual ゆえ抽出 core は縮小 (spec §7:102 「300-800 touched」整合)。**core module (route_executor.py) を ≤800 に収め、byte-repro harness は test file に分離**。超過時は %12 checkpoint で split 判断 (env-core precedent 1329L)。

**✅ Q2 env-core cross-node edit — ⭐Rs 決定 = A (2026-07-07 02:37, AskUserQuestion, `bad0d25204`):** staged-chain 権限を「**flag-gate default-off なら route-executor が前段 COMPLETE component の source を cross-node 編集可**」と正式拡張 (%12 の旧 Q2 越権 [E3] = Rs 認可で解消)。**方式 = A (3 箇所全て flag-gate default-off)**:
- (1) servo (`_apply_actions_batch`) / (2) C2-clip (scene builder `add_target_clip_c2`) / (3) route-swap (`self._route`:309) を **全て新規 flag で default-off**。
- **legacy-config {C1-only + stub + servo-off + C2-off + swap-off} が env-core ⑨a′ 25/81 EXACT を再現 = COMPLETE byte 保全** (B⑨a′ 再regression が **3 箇所全 default-off** を非回帰検証、servo だけでない)。
- **C2-on/servo-on run は「⑨a′ preserved」呼称禁止 → 「Layer-B re-BASELINE (new predicate, non-conservative)」**。
- env-core node は **COMPLETE 維持 (re-open 不要)**、編集は route-executor design-gate + 5体 + 層5 が cover。env-core node に cross-ref annotation 済 (%12 02:36)。

**⚠ IK stack transitive-closure manifest (v1.4, 5体 CRIT1 で physics_step 矛盾解消 + CC4-CH5 cite 訂正):** route_executor.py に **verbatim copy** = {`ik_move_both`:1958 / `solve_ik_dual`**:1854** / `_solve_ik_dual_rot`:5171 / `_rot_quat_rx`:5156 / `_cable_local_pitch`:5161} + monkeypatch install/restore (:5214-5215/:5343 を **route_executor の globals** に対して実行)。**⚠ `physics_step`:1790 = CRIT1 で判定** — copy (`_demo_rec`:1780 / `_physics_state_buffer`:1768 / `_ARM_OVERWRITE_IDX` が route_executor の globals へ解決) **or** 外部 capture-loop で wrap (§4 step2); **どちらか一方に確定** (旧 v1.3 の copy/reuse 両掲 = CC2-CH1/CC3-CH2 の split-brain recorder bug、撤回)。**import-reuse** (IK 非依存、byte-safe、_demo_rec 非参照) = {`get_ee_positions`:1945 / `update_kinematic_bodies`:1752 / geom helpers / IK objective classes / 定数 `DEVICE`/`IK_ITERATIONS`/`IK_STEP_SIZE`/`STEPS_PER_CM`/`SIM_SUBSTEPS`/`SIM_DT` 等}。5体で transitive closure grep 検証 + 静的 tripwire (§9)。

---

## §3. DoD (charter §1 = node state.md:6-15、byte-repro = 全項前提)

**⚠ v1.2 = 2-layer 分離 (%12 disposition 01:22 `dfe5dd0920`、pre-check CRIT1/2 fold): DoD① substrate 混同 (env-core 経由 58/81) を撤回。**

#### Layer A — 抽出忠実 (PRIMARY, env-core 非依存, conservative-definite = 真の先祖返り guard)
| # | 項目 | bar / 判定 |
|---|---|---|
| **A① byte-repro (PRIMARY)** | RouteExecutor `run_route()` を **monolith substrate (SIM_SUBSTEPS=10 + copied IK + 実 grip) 経由**で canonical 81-grid → **⚠ v1.4 (5体 CRIT2, %12 E2 own): 2 量で bar 分離** — **(i) HARD L∞=0 = ee_tgt_pos の CPU-deterministic scripted phase のみ** (grasp/lift/transport/fixed-geometry seat = 抽出対象 route logic; ≥1 不一致 = 抽出 infidelity = build FAIL) **∧ (ii) ee_tgt + joint_q = tolerance-band + flag+carry** (⚠v1.5 re-pre-check ISSUE2: **C2 re-grasp ee_tgt も GPU 由来** — argmin over `state.body_q[cable_bodies]`:5127-5138 [ANTI-REVERT] ゆえ GPU#562-stochastic; joint_q は全域 GPU IK 出力。両者 A①-pre 分類 cell で tol-band) **∧ (iii) verdict strict_v2 EXACT** (安定 cell)。**前提 = A①-pre self-repro (§4 step1b)** が ee_tgt/joint_q 各々を per-cell CPU-det/GPU-stochastic 分類。「conservative-definite」= CPU-det phase の ee_tgt HARD leg 限定。env-core 非経由ゆえ抽出のみ isolate。 |
| **A② ⑦ handover-fidelity** | `reset_to_phase(k)` per-world 復元 (arm qpos/qvel + **cable joint state + `_per_world_fk_jq`**, Issue6) の 2 判定: (i) **round-trip** L∞≤1mm/1mm·s⁻¹ (restore 決定性) **∧ (ii) bank-vs-monolith spot-check** (canonical center cell で banked phase-k state を monolith の同 G-boundary live state と照合、Issue7 = 「handover-fidelity」が bank 忠実性を bound) |
| **A⑤ wall/spacer exact predicate** | mjModel geom introspection: wall-dist≤0.5mm spacer-excluded (`c2_seated_honest`:5580 一致、substrate 非依存) |
| **A⑧ ⑬ enabler のみ** | recorded-target-replay + C1-escape non-vacuous cell ≥1 (pre-snapdown 36/81); **⑬-VERDICT = D-2 trainer defer** |

#### Layer B — substrate-transfer (env-core substrate + 実 grip, 非保守, bar=実測 [58/81 仮定禁止])
| # | 項目 | bar / 判定 |
|---|---|---|
| **B③ ⑨b online-numerator** | env-core substrate (**4-substep 維持** + gripper servo dynamic close = §2 drive-loop 拡張) residual≡0 × 81 live → **strict_v2 実測** (58/81 と**仮定禁止**、%12 Q3)。⚠ **v1.4 (5体 CC3-CH3): divergence を per-axis 符号付きで報告** — {**grip-hold** (⭐v1.5 %12 必須軸: cable が route 全域で把持維持されるか — drop = substrate-transfer finding) / grip-force / seat-depth / reach} 各軸を **conservative (env-core<oracle=RL が recover) / non-conservative (env-core>oracle=over-optimism、高 fidelity/実機 確認要) / unknown-要判定**でタグ (旧「recover すべき量」= deficit 方向 presume 撤回)。⚠ **grip-hold は viability 軸** (re-pre-check ISSUE4: 4-substep での dynamic close が **そもそも把持できるか** = magnitude でなく可否; grip 失敗時に force-design 再訪 trigger)。**substep 4→10 決定 = Rs-level post-data** (今は 4 維持で empirically-gate) |
| **B④ ⑥ full-fire live** | env-core + dynamic gripper servo (実 grip) → G2-G6 live fire。bar=実測 |
| **B⑥ C2-seating 動画 gate** | 実 C2 groove scene で C2 着座 §運用14 CC frame-check + video-analyst + Rs verdict (Rs 約束済) |
| **B⑦ CABLE_XY_OFFSET wiring** | 実 route が per-cell offset 消費 (DR/⑨b 前提) |
| **B⑨a′ env-core 非回帰 (v1.4, 5体 CC5-CH1, ⭐Rs=A)** | 3 箇所 cross-node 編集 (servo/C2-clip/route-swap) 全 default-off での **legacy-config {C1-only + stub + servo-off + C2-off} が env-core ⑨a′ per-cell EXACT 25/81 を byte-identical 再現** = COMPLETE 保全 (servo だけでなく 3 箇所全 default-off を検証; env 25/81==offline==ceiling の frozen 値)。**flag-on の C2-scene run は「Layer-B re-BASELINE (new predicate, non-conservative)」**(「⑨a′ preserved」呼称禁止 = partial-truth 回避)。**⭐v1.6 item⑨ 要件2 追加 (%12 05:38): B⑨a′ scope に「reset_to_phase contract 変更 (widened `k: int\|torch.Tensor` 署名 + all-zeros default)」を明示追加 → flag-off/stub path で env-core ⑨a′ 25/81 + ⑩ + ⑪ が COMPLETE を EXACT 再現を gate item 化 (built-model geom + numeric 両方) = contract 変更が env-core COMPLETE を regress しない HARD guard** |

**分子完全性 (§運用29):** 分子 conjoin = **strict_v2 (C1-retention leg ∧ C2-seat leg 両方)**。cover しない leg = **trainer 段 policy 学習成果** (本 node scope 外、明示)。SR claim を route-executor で出さない (SOMA:717、over-claim 禁止)。

**⚠ conservatism 方向 (GROVE v1.1、2-layer):** Layer A (verdict+trajectory byte-identity) = 抽出忠実性について **conservative-definite** (先祖返り guard)。Layer B (substrate-transfer) = **非保守、bar=実測** = 58/81 からの divergence 自体が finding (%12 Q3)。**substrate-transfer risk は P2 residual-RL 前提に material** → %12 が Rs へ loud 提起 (magnitude = Layer B 実測、substep 決定 = data 後)。

---

## §4. byte-repro regression harness 設計 (D-1=C の一次 guard、先祖返り防止)

**⚠ v1.2 (pre-check CRIT1 fold):** 旧 §4 の「module leg = env-core 経由」は **別 substrate (RL_SIM_SUBSTEPS=4 + fingers-open) ゆえ抽出忠実性を isolate 不能** → 撤回。byte-repro を **Layer A (抽出忠実、monolith substrate 経由) の一次 guard** に再定義。

#### Layer A harness — 抽出忠実 (env-core 非経由、conservative-definite)
**目的:** 抽出 delta ゼロを機械証明 (env-core substrate から isolate)。
1. **reference leg (locked, 不触):** `_run_mujoco_grasp_route`:3692 を canonical 81-grid (w0e_81rerun_snapdown harness) × cuda:0 × FON_V1 で走らせ、per-cell **golden = (a) strict_v2 verdict 58/81 + (b) per-step recorded targets `ee_tgt_pos_l/r` + `joint_q`** (banked provenance `w0e_81rerun_snapdown_0537`)。
1b. **⚠ A①-pre self-reproducibility gate (v1.4, 5体 CRIT2, [CHANGE] を gate):** locked `_run_mujoco_grasp_route` を **N≥3 回 同一 cell × cuda:0 × INIT pinned** で走らせ、per-cell `ee_tgt_pos`/`joint_q` の oracle-vs-oracle L∞ を測定 → 各 cell を **float-exact-reproducible / GPU-stochastic** に分類。**これで L∞=0 が discriminator として妥当な cell を確定**してから module leg 照合。(ee_tgt は CPU-deterministic ゆえ全 cell L∞=0 期待、joint_q は C2 re-grasp cell で noise-floor > 0 を実測)。
2. **module leg (新):** `RouteExecutor.run_route()` を **monolith 自身の substrate (SIM_SUBSTEPS=10 + copied IK + dynamic grip) 経由**で同一 81-grid × 同一 device/pin で走らせる (**env-core 非経由**)。⚠ **capture (v1.4 CRIT1):** per-frame `ee_tgt_pos`/`joint_q` の記録は **route_executor 自前 recorder** で行う — `_demo_rec.sample()` は `physics_step`:1846 内ゆえ、physics_step を **copy** (自前 _demo_rec 解決) **or** run_route が physics_step を **外部 wrap し同一 capture point (:1846 相当、post-substep) で記録** (9-frame-offset guard [[feedback-verify-dump-capture-point]])。**physics_step を copy/reuse で両掲しない** (manifest 訂正)。
3. **assert (v1.4 3 段):** **(i) ee_tgt_pos L∞=0** (全 cell HARD、≥1 不一致=抽出 infidelity=build FAIL) **∧ (ii) joint_q L∞ ≤ A①-pre noise-floor** (float-exact cell) / **flag+carry** (GPU-stochastic cell) **∧ (iii) verdict strict_v2 EXACT** (安定 cell)。joint_q の GPU noise を抽出 infidelity と誤断しない (5体 CRIT2)。
4. **namesake guard:** reference は production `_run_mujoco_grasp_route`:3692 のみ (全列挙: `do_p1_grasp`:2227 / `run_episode`:2746 / `_run_mujoco_grasp_episode`:3036 / `_run_mujoco_grasp_engage_episode`:3230 / `_run_mujoco_episode`:7478 と混同禁止)。
5. **determinism pin (v1.4, 5体 CC2-CH3 で層訂正):** Layer A (monolith substrate) の stochastic source は **GPU float-order (#562) のみ** (canonical route script に unseeded np.random 無 — 唯一の np.random:8321 は `RandomState(seed)` = seeded)。∴ Layer A 決定性制御 = cuda:0 canonical のみ + A①-pre self-repro (step 1b) で GPU noise-floor を実測。⚠ **`INIT_XY_NOISE=0` は env-core (`newton_route_env.py:250/:590-592`) の pin ゆえ Layer B contract へ移動** (旧 v1.3 の「monolith :591」cite は誤 = CC2-CH3、:591 は z-height loop)。
6. **HIGH4 fold (no-global-mutation, v1.5 stale 訂正):** 新 module は `test_newton_clip_routing` の module global (`globals()["solve_ik_dual"]`) を **runtime mutate しない** (不触 file 契約)。C2 re-grasp の rotated IK = **自前 IK stack verbatim copy 確定** (§2、v1.3 決定; 「explicit solver pass」は ik_move_both:1961 署名変更要ゆえ **不採用確定** — 旧「copy-vs-extract 精査」framing 撤回)。5体 = copy の float-exact 忠実性 + transitive-closure 完全性を精査。

#### Layer B setup — substrate-transfer (env-core substrate、非保守、bar=実測)
**目的:** env-core substrate (4-substep + gripper servo) での route の live 挙動を **実測** (先祖返り guard でなく transfer 特性測定)。
1. env-core + §2 gripper-servo drive-loop 拡張で residual≡0 × 81-grid live → strict_v2 実測。
2. **58/81 と仮定せず**、Layer A golden との divergence を per-cell 記録 = substrate-transfer finding (residual-RL が recover すべき量、%12 Q3)。
3. substep 4→10 は**変更せず 4 維持**で measure (magnitude で substep 決定 = Rs-level post-data)。

**conservatism 方向 (GROVE v1.1):** Layer A = 抽出忠実性について **conservative-definite** (verdict+trajectory byte-identity)。Layer B = **非保守** (substrate-transfer divergence 自体が finding、over-claim 禁止)。

---

## §5. stub 契約 v1 実装方針 (env-core interface `rc.RouteInterfaceV1` を実装)

env-core `NominalRouteStub`:178 が実装する契約を `RouteExecutor` が実装 (interface 不変、差し替えのみ):

```
class RouteExecutor(rc.RouteInterfaceV1):
    reset_to_phase(k: int | torch.Tensor) -> None   # ⭐v1.6 item⑨ (%12 05:38 要件1): widened 署名 = scalar(all-world broadcast) OR per-world tensor; default all-worlds-phase-0 = 現 reset_to_phase(0) byte-neutral (env-core :1120 caller 非破壊、scalar 拒否せず)
        # 実 state-bank: phase k = 6 coarse G (%12 CONCUR 00:32: reset_to_phase(k) の k = coarse G semantics; spec:29 curriculum start-mix {P0,G1..G5-eps} 消費者に一致、15-fine は消費者無=YAGNI) の precomputed qpos/qvel を復元
        # env-core :1120 は no-op stub → 実配線。⑦ handover-fidelity (L∞≤1mm/1mm·s⁻¹) の source
    step_target(t) -> (target_6d, phase_id, grip_2, is_dual)
        # target_6d = 実 route の per-step base 絶対 target (fork-(iv) 6D abs, 非累積)
        #   = monolith の phase 別 target 計算 (tgt/tgt2/_w0e_guarded_cx/seat k/8/ANTI-REVERT argmin) を faithful 抽出
        # phase_id = base-owned G1-G6 live clock (earned-predicate 非依存の base scripted, CC2-CH4)
        # grip_2 = per-arm scheduled grip 2-vector (base script single-source, CC5-2)
        # is_dual = is_dual_grip_window boolean (base script single-source, env 再導出禁止)
    # + recorded-target-replay mode (mode=ROUTE_MODE_*): route_demo_raw.npz の ee_tgt_pos_l/r replay
    #   = ⑬ enabler + ⑥/⑩ whole-route DoD 用 (CC5-2 iii、env-core :192 recorded_targets 既配線)
```

**state-bank 実装 (spec §2-F2 (b) precomputed phase-k、%12 CONCUR = 6 coarse G):** monolith を各 coarse G 境界 (6 点: G1 grasp/G2 lift-transport/G3 C1-seat/G4 unclamp-guide/G5 C2-transport/G6 C2-seat) まで実行 → qpos/qvel snapshot を bank → `reset_to_phase(k)` で復元。⚠ **Newton 全 world 一斉 step 制約**と両立する唯一の AC-reset-pattern 互換案 (spec:29 (b))。DR は bank cell に量子化 (文書化、spec pin ③)。prefix 物理 overhead (G5−ε ≈ 7000 frames) は throughput smoke に計上。`reset_to_phase(k)` の k 公開 semantics = coarse G; 内部で `_ph` 15-label に沿った fine bank が faithful/安価なら実装可だが expose は coarse G (5体 [VERIFY] 対象、over-provision 回避)。

**⚠ MED6→CRIT4 fold (data-flow spec, v1.4 5体 CC5-CH2 で FULL per-world 化):** (a) **per-world k + FULL per-world state 復元**: `reset()` に per-world k を thread、`reset_to_phase` は `_reset_worlds` の authoritative re-pose の**後**に per-world で以下を全て上書き (env-core :611-627 path と compose; global-k scalar :1120 でなく):
  - (i) arm qpos + (ii) arm qvel [banked, 0 でなく] + (iii) cable joint state [G3-G6 = routed/gripped] + (iv) `_per_world_fk_jq[w]` [warm-start :691 stale 回避]
  - ⚠ **v1.4 追加 (CC5-CH2、これ無しで phase-k rollout が即発散)**: (v) **`episode_length_buf[w]` ← phase-k 開始 frame** [route-clock; 現 `reset()`:1119 は [:]=0 → `_pull_route` が t=0 で `step_target(0)`=phase-0 target を返し arm yank] / (vi) **`_target_seg_indices_r/l` を cable 再pose 後に再計算** [:629-633 は settled cable 由来 stale] / (vii) `_prev_phase_id`/`_phase_entry_step` ← phase-k / (viii) `_g_latched`/`_g6_sustain`/`_contact_loss_count` ← banked [G4+ world が past-gate 再earn/spurious drop 防止] / (ix) `_ee_target_r/l` ← phase-k EE / (x) `_prev_clamp_*`/`_prev_seg_*` ← banked [first-step orientation-delta obs]。
(b) **DoD② 検証 (Issue7 + CC5-CH2)**: round-trip (restore 決定性) **∧ bank-vs-monolith spot-check** (canonical center cell) **∧ ⭐1-step-after-reset divergence test** [phase-k banked → zero-action で 1 step → EE/target/phase_id が monolith の同 G-boundary+1 と一致; round-trip は self-consistent snapshot に blind ゆえ本 test が gap に sensitive]。(c) **self.state SSOT**: closure→method で `self.state` は monolith の全 `state` rebind を mirror + **write-barrier (single setter, physics_step 後 assert, CC2-CH5)**。

**⚠ Layer A 実行モデル (re-pre-check Issue3):** `RouteExecutor` は 2 面を expose — **(1) `run_route()` = self-driving** (**copied** ik_move_both + **import-reused** physics_step [IK 非依存] を internal に呼ぶ per-waypoint orchestration; speed_factor/converge_mm/physics-burst 数/grip frame を保持) = **Layer A byte-repro の subject** (monolith substrate と同一 code path) / **(2) `step_target(t)` = per-step facade** (env-core が RL step 毎に target_6d を pull) = **Layer B の subject**。両者は **target-computation 関数を共有** (facade は self-driving の per-step 断面)、共有層を byte-check。∴ Layer A は self-driving orchestration を byte-validate、facade の target 値は共有ゆえ by-construction 一致 (per-waypoint vs per-RL-step の乖離を Layer 境界に封じ込め)。

**grip schedule single-source (CC5-2):** is_dual_grip window + arm-role (reaching=full σ / gripping=σ-cap) は **base grip-schedule から導出** (env 再導出 phase→window table 禁止 = env-core NEW-D と同一 deterministic source、boundary mislabel→drop 防止)。

---

## §6. [DESIGN-GATE] (直交, code 前必須) — 実行予定

- **`/geometric-design`** (C2 groove scene): C2 clip 配置 (ROUTE_C2_XY canonical (0.40,0.000) 間隔倍化 CLIP2_Y=0)、C2 groove geometry (walls/spacer split for wall-dist≤0.5mm)、C1↔C2 間隔と cable span (92.4mm) の幾何整合、C2-over-solid vs C1-over-void 床 parity ([[reference-clip-positions-vs-grasp-void-geometry]])。6 ステップ出力 (実測・制約・断面図・トレード・感度・因果連鎖)。
- **`/reward-design`** (軽 — route/predicate 不変): route-executor は G1-G6 predicate を**変更しない** (env-core spec v1.5f が SSOT)。到達可能性は **live route で predicate が earn される**ことの確認のみ (predicate code 不変ゆえ artifacts v1.3 の再 discharge は差分のみ)。
- **`/force-design`** (v1.4 追加判断、%12 委任 02:37 — servo が実 grip force 導入): **判断 = skip (力階層 inherited/不変)**。理由: grip force/stiffness/contact params は **monolith から verbatim inherited** (Layer A の IK/grip copy 内 + env/task_config の gripper actuator params 不変) = **新規 force 設計なし** (geometric-design Step0 reuse-before-build と同型)。⚠ 唯一の新要素 = env-core **4-substep での servo close contact 動態** = **Layer B measurement 事項** (force param 設計でなく substrate-transfer 実測、B③ signed-divergence の grip-force 軸)。材料的乖離が実測されたら force-design 再訪 (substep 決定と同じ Rs post-data)。∴ 本 gate skip + Layer B carry。
- **`/pre-check`**: 抽出失敗モード (byte-repro capture / L∞ bar / state-bank fidelity / grip timing / C2 scene artifact) を Claude sub-agent で検証。BLOCK なら redesign→re-run。**v1.4 = re-pre-check + full 5体 再走 (前回 FAIL 復帰 + env-source 新 surface、%12 02:37)**。
- **両 PASS でなければ [RULE-CHECK]→build に進まない** (§運用2)。

---

## §7. gate chain (L3、charter §7 precedent)

```
[DEFINE ✓ charter] → [TASK]/[L-TRIAGE]=L3 ✓ (§1) → build plan 起草 ✓ (本 doc)
  → [DESIGN-GATE] (/geometric-design C2 + /reward-design 軽 + /pre-check)
  → %12 checkpoint (code 前)
  → [VERIFY] 5体 CC Debate (変更計画 diff, task-start f0bd54992c..HEAD)
  → [RULE-CHECK] Tier0-3
  → [CHANGE] build (route_executor.py + C2 scene + env 統合 + byte-repro harness)
  → [RUN] smoke: byte-repro 58/81 EXACT (①) + ⑦ handover + ⑨b online + ⑥ full-fire
  → [層3 機械] + [層5 多視点 幾何/物理/SSOT] + [層2 事後 debate on-disk]
  → C2-seating 動画 gate (Rs, 実 C2 groove scene)
  → node COMPLETE (cascade: parent T-ROOT-optE-route-dapg-C1C2 の子)
```

**checkpoint 毎に %12 (w2:p4) へ ping** (charter 指示)。dispatch = `herdr agent send w2:p4 "$(cat ...)"` + `herdr pane send-keys w2:p4 Enter` (2-step, backtick-hazard 回避)。

---

## §8. open items / design questions (checkpoint + 5体 [VERIFY] 対象)

1. **抽出粒度 = ✅ DECIDED (v1.3, re-pre-check CRIT1):** IK stack (ik_move_both + solve_ik_dual + _solve_ik_dual_rot + _rot_quat_rx) は **自前 module に verbatim copy** (import-reuse 不可 = 1-ULP monkeypatch ゆえ、§2)。IK 非依存の module-level helper (geom/_set_gripper_target) のみ import-reuse。27-closure per-closure 分類 (抽出 7 [target/IK] / residual 20 / dead 24) + inline target (W0-e/seat k8/ANTI-REVERT) copy は byte-repro (Layer A trajectory) が drift guard。**5体で copy 忠実性 (float-exact) + closure→method state 保持を精査。**
2. **state-bank 粒度 = ✅ RESOLVED (6 coarse G、%12 CONCUR 00:32):** `reset_to_phase(k)` の k = coarse G semantics (spec:29 curriculum start-mix 消費者に一致、15-fine は消費者無=YAGNI over-provision)。内部 fine bank は faithful/安価なら実装可だが expose は coarse G。5体 [VERIFY] で残置。
3. **byte-repro tolerance:** strict_v2 verdict は boolean per-cell ゆえ EXACT-match が自然。ただし GPU#562 非決定で verdict-flip する境界 cell の扱い (§4 手順5) = **N≥3 再走で安定 cell のみ golden、非安定 cell は flag+carry**。bar 緩めでなく非決定性の honest 会計。
4. **C2 groove scene の 3mm proxy 非保守 (charter §8):** 剛体 clip 非保守 carry を C2 でも承継 (spec §8)。実機前に再訪 (over-claim 禁止)。
5. **recorded-target-replay の horizon cadence:** monolith 7709 frame → env horizon 900 の resample (env-core :192 で既配線、cadence 整合を Layer A trajectory 照合で確認)。
6. **✅ RESOLVED — substep alignment (Layer B, %12→Rs, v1.2):** env-core `RL_SIM_SUBSTEPS=4` vs oracle `SIM_SUBSTEPS=10` の乖離 = **Layer B で 4 維持のまま実測** (変更せず empirically-gate)。substep 4→10 変更 (fidelity↑ vs RL throughput↓) の**決定 = Rs-level post-data** (magnitude 判明後)。substrate-transfer divergence 自体が P2 residual-RL 前提に material → **%12 が Rs へ loud 提起**。
7. **gripper-servo 忠実性 (Layer B, 5体):** env-core drive-loop の dynamic servo close cadence を monolith (cage 30 + 12×12 ramp + 40 settle @10-substep) から env-core (10-frame/4-substep) へ再表現 = contact onset shift 可 (Layer B 実測範囲、Layer A は monolith substrate ゆえ非該当)。

---

## §9. risks / conservatism carries (charter §8 承継)

- **Rs-LOCKED file 関与 = 最大 risk (先祖返り class):** byte-repro regression = 一次 guard。抽出中に「挙動を変える」判断が出たら **STOP → BLOCKED_FOR_USER (Rs)** (§1 high-care)。
- **byte-repro の device 依存:** cuda:0 canonical のみで判定 (cpu = read-only proof、[[project-canonical-route-device-fragile-cpu-vs-cuda]])。
- **namesake hazard (%12 訂正、全列挙 guard):** production `_run_mujoco_grasp_route`:3692 のみ cite。混同禁止の全 legacy 列挙 = `do_p1_grasp`:2227 / `run_episode`:2746 / `_run_mujoco_grasp_episode`:3036 / **`_run_mujoco_grasp_engage_episode`:3230** (旧 doc の `_grasp_engage_episode` は `_run_mujoco_` prefix 欠 = 訂正) / `_run_mujoco_episode`:7478。byte-repro harness は :3692 を明示 cite (C 案で二重 SSOT ゆえ特に重要、[[reference-test-newton-legacy-vs-production-route-namesake-functions]])。
- **state-bank fidelity (⑦):** qvel は live state から取得 (recorder に qvel 無、spec:29)。L∞≤1mm/1mm·s⁻¹ を DoD② で機械証明。
- **oracle/OG/trainer は本 node 非該当:** SR/学習成果 claim を route-executor では出さない (SOMA:717、trainer/campaign 段、over-claim 禁止)。
- **⑬-VERDICT defer (D-2):** route-executor は ⑬ enabler のみ。residual≠0 VERDICT は trainer 段実 policy (合成摂動の representativeness risk 回避、Rs 23:5x)。
- **⚠ substrate-transfer risk (v1.2, pre-check CRIT1/2):** env-core substrate (4-substep + gripper-servo) の live route は oracle (monolith 10-substep + dynamic grip) と divergence 可 = **Layer B 実測** (非保守、**58/81 仮定禁止**)。**P2 residual-RL 前提に material** → %12 が Rs へ loud 提起、substep 決定 = data 後。Layer A (monolith substrate) が抽出忠実性を conservative-definite に guard するため、substrate gap は抽出 infidelity と分離済。
- **⚠ no-global-mutation + self-owned IK stack (v1.3, HIGH4 + re-pre-check CRIT1):** 新 module は locked file の module global (`globals()["solve_ik_dual"]`:5214 monkeypatch) を **runtime mutate 禁止**。⚠ **旧「tilt=0 で masked」は FALSE (撤回)**: golden C2 re-grasp は `_solve_ik_dual_rot` (`_rot_quat_rx` sin/cos) 使用、literal `solve_ik_dual`:1898 と **1 ULP 差 (実測 confirmed)** → import-reuse ik_move_both では Layer A byte-identity 不能。∴ **IK stack を自前 module に verbatim copy** し in-module 解決 (§2 決定)。「explicit solver pass」は ik_move_both 署名 (:1961 solver=physics) 変更要ゆえ **不採用**。非 canonical (C2_TILT_SIGN=1) smoke でも wiring 実証。
- **⚠ two-copy IK drift gate (v1.3→v1.4, 5体 CC5-CH3 で静的化 + CC4-CH4 banner):** IK stack が copied (oracle in-file Rs-LOCKED frozen :5290 + route_executor copy) → **route_executor copy のみ drift 可**。⭐ **v1.4 = 静的 tripwire を一次 gate 化**: `inspect.getsource`/`ast.unparse` で copied IK 各関数が oracle と string-equal を **layer-3 mechanical test (no-GPU, deterministic, `test_route_geometry_sync.py` 型)** で assert → drift が cheap deterministic test で fail。Layer A byte-repro (cuda:0, GPU-expensive) 再走は二次確認に降格。+ route_executor の IK copy に **banner「MIRROR OF Rs-LOCKED :5156-5343 — Layer-A re-repro + Rs なしに編集禁止」** + golden provenance hash (`w0e_81rerun_snapdown_0537`) を gate に pin (golden swap 検出)。
- **⚠ invariant-enforcement scope 訂正 (v1.4, 5体 CC4-CH2):** 「byte-repro が invariant を structural enforce」は **Layer A (抽出 vs monolith) 限定**。servo/C2/4-substep の Layer B path は byte-repro 非経由ゆえ別基底要: **DUAL-ARM = servo が per-arm `grip_2` 2-vec で両腕駆動** + **no-kinematic-trick = ⚠v1.6 §10.1 governs (grasp_actuation=True で gripper を model-level actuator/4-bar 化 = kinematic pin でない、:738 から全16 gripper coords 除外、route grip_cmd = drivers[6,10,20,24] joint_target_pos; v1.5 drive-loop servo は inert ゆえ撤去)。[v1.5 historical] gripper DOF を `_ARM_OVERWRITE_IDX`:1776 pattern で :738 kinematic write から除外 + PD `control.joint_target_pos` 駆動** (joint_q.assign 上書きしない、monolith :1826-1828 proven; ⚠v1.5 re-pre-check CRIT = env-core :738 の全 28-slice write が gripper DOF を kinematic 上書きしていた欠陥を fix) を Layer B/B⑨a′ check に明記。
- **✅ env-core cross-node edit (v1.4, ⭐Rs=A 02:37): 3 箇所 flag-gate default-off** (5体 CRIT3 解消)。gripper-servo (`_apply_actions_batch` :724-727 gated pre-loop rewrite) + C2-clip (scene builder `add_target_clip_c2` default-False) + route-swap (`self._route`:309 default-stub) を全て default-off flag 化。**legacy-config {C1-only + stub + servo-off + C2-off} が env-core ⑨a′ 25/81 EXACT 再現 = COMPLETE byte 保全** (B⑨a′ が 3 箇所全 default-off を非回帰検証)。C2-on run = 「Layer-B re-BASELINE (new predicate)」(「⑨a′ preserved」呼称禁止)。**MED9 blast-radius (CC4-CH3): 共有 `newton_skill_env_base` の grip/AR/AC scene build が C2-clip flag default-off で byte-unchanged を grep-confirm** (base は既に add_target_clip flag-gate :1491)。env-core node COMPLETE 維持 (re-open 不要、cross-ref annotation 済)。

## §10. v1.6 fold — servo-scope escalation DISPOSITION Rs=A (⭐governing grip 機構; %12 disposition 05:17 / plan-ACK 05:23、node commit `9b9a41604c`)

**§10 が v1.6 の grip 機構を governs。§2(b) / §9 の v1.5 "drive-loop servo" 記述は SUPERSEDED (historical、pointer 済)。PLAN = %12 APPROVED (05:23)。**

### §10.1 grip 機構 = grasp_actuation flag-flip (v1.5 drive-loop servo 撤去)
**根本訂正 (full 5体#2 LOAD-BEARING CRITICAL, CC2/3/4 独立一致):** v1.5 の drive-loop servo (:738 gated pre-loop で joint_target_pos write) は **駆動 actuator が無く物理的 inert = silent grip 失敗**。route call `newton_route_env.py:339` `build_multiworld_scene(...)` が `grasp_actuation` 未渡し=**default False** → gripper POSITION actuator (base:1594-95 ke/kd) + 4-bar connect eqs (base:1586-) + condim=6 + table VOID (base:1738-1769) が全て `if grasp_actuation:` (base:1586 / :1738) 配下ゆえ **env-core で未 build**。
**正機構 (§運用28 3-CLAIM CONFIRMED):**
- **flag-flip:** route call:339 に `grasp_actuation=<flag>` kwarg 追加 (sig base:1484 が既に `grasp_actuation=False` param 受理 = **signature 変更不要**、%12 de-risk 05:23)。**default-off = env-core COMPLETE の grasp_actuation=False 認定を byte-preserve** (4th flag、Rs=A `bad0d25204` cross-node flag-gate 範囲内)。flag-on = **proven base:1586-1740 の gripper actuator + 4-bar + condim6 + table VOID を model-level build** (= monolith `build_scene(grasp_actuation=True)` mirror、`test_newton_clip_routing.py:3715` hard-assert = 0.716 MOTION STANDARD substrate)。
- **grip drive:** route grip_cmd = `control.joint_target_pos` の **drivers [6,10,20,24]** (GRIPPER_DRIVER_JOINT_IDX + right-arm offset) を schedule で dynamic close (monolith :1826-1828 proven POSITION-drive)。follower DOFs は 4-bar equalities で従動。
- **kinematic-write 除外 = 全16 gripper coords** (finding#5 fold): grasp_actuation=True で gripper は actuator/4-bar 駆動ゆえ、:738 の 28-slice kinematic write から **GRIPPER_JOINT_RANGE[6..13]×2arm = 全16 gripper coords を除外** (drivers + followers 両方)。旧 v1.5「6/10/20/24 drivers のみ除外」= follower kinematic pin = partial trick、**撤回**。除外しないと model actuator を kinematic write が上書きし inert 再発。
- **servo-off (default) = 全 28-slice kinematic write 維持 = byte-identical** (env-core COMPLETE 保全)。
**3 findings 同時解消 (v1.5 より clean):** (i) inert-servo CRIT = gripper model-level 物理化→grip_cmd が既存 POSITION actuator 駆動 (ii) CC4 no-kinematic-trick #5 = grasp_actuation wire = Pattern-7 (kinematic finger 再導入禁止) 遵守 (iii) finding#5 全16 除外 = actuator 駆動ゆえ正当。
**LOC:** flag kwarg (~2) + gripper-coord exclusion (~10-20) + grip schedule (③ verbatim cadence) ≪ v1.5 の ~80-140。

### §10.2 full 5体#2 HIGH/MED 10項 fold
| # | finding | disposition (v1.6) |
|---|---|---|
| ① | IK closure verbatim不能 (`_solve_ik_dual_rot`:5171 / `_cable_local_pitch`:5161 が route-locals `_ROT`/`state`/`cable_bodies` を close over → verbatim copy 不能 + string-equal tripwire 無効) + transitive-closure 5 globals 未列挙 | **mechanical rewrite** (route_executor の locals へ re-plumb) + **semantic-equivalence check** (string-equal でなく AST/behavior 照合、§9 two-copy gate を semantic 化)。5 globals (`MAX_MOVE_STEPS`/`JOINTS_PER_ARM`/`GRIPPER_JOINT_RANGE`/`EE_BODY_OFFSET`/`FRANKA_NUM_JOINTS`) を §2 IK-stack manifest に追加 |
| ② | reset_to_phase が `_last_ik_resid` (obs[55:57] feeder :912-913) + telemetry (`_last_executed_residual`/`_last_projection_mode`) 省略 → A②/⑦ が obs で vacuous | §5 reset_to_phase per-world 復元 list (v1.4 (v)-(x)) に `_last_ik_resid` + telemetry 追加 |
| ③ | production grip cadence (grip_2 = monolith 214-frame close :4255-4271) の RL-cadence 再表現 未仕様 (「by-construction 一致」は arm target のみ真) | route grip scheduler = monolith :4255-4271 の **214-frame close cadence を verbatim replay** (frame-indexed joint_target_pos ramp)。Layer A byte-repro に **grip DOF trajectory を含める** |
| ④ | HARD L∞ phase 分類誤 (grasp-Z:4276 + C1-seat-X:4512 も GPU-argmin、C2 re-grasp だけでない → CPU-det phase set 縮小) | HARD L∞=0 (ee_tgt_pos) を **argmin-free scripted phase のみ** に再限定 (grasp-Z/C1-seat-X/C2-regrasp = tol-band+flag+carry)。A①-pre self-repro (§4 step1b) が per-phase 分類を実測 |
| ⑤ | `_ARM_OVERWRITE_IDX` = 全16 gripper coords | **§10.1 flag-flip で RESOLVED** (actuator 駆動ゆえ全16 除外が正当) |
| ⑥ | reset_to_phase は reset(k=0) のみ呼、auto-reset done-path (:1135-1136) が phase-k 未呼 → curriculum start-mix が training loop で dead | auto-reset done-path にも per-world phase-k 配線 (reset_to_phase を done-path 経由でも呼、per-world k carry)。⚠ curriculum 前提は D-2=trainer 段ゆえ本 node は **enabler wiring のみ (⑬)** |
| ⑦ | servo grip-command (`control.joint_target_pos` drivers) が reset されず cross-episode leak | reset_to_phase で drivers [6,10,20,24] を `GRIPPER_DRIVER_OPEN_RAD` に reset (§5 復元 list 追加)。⚠ flag-flip 後 leak 対象 = actuator target のみ |
| ⑧ | monkeypatch (:5214 install / :5343 restore) に exception-safe restore 無 → long-lived module で state leak | **try/finally で restore 保証** (route_executor globals に対して、§2 IK-stack manifest) |
| ⑨ | reset_to_phase 署名 scalar→per-world = `RouteInterfaceV1` contract 変更 (stub も touch) | **✅ %12 checkpoint 05:38 ACCEPT + 3 要件** (blast radius = env-core `newton_route_env.py:1120` reset_to_phase(0) の 1 caller + no-op stub のみ = contained): **要件1 (backward-compat 署名)** = `reset_to_phase(k)` を widen `k: int \| torch.Tensor` (scalar=all-world broadcast OR per-world tensor 受理、scalar 拒否せず = env-core reset() path 非破壊、`route_env_config.py:158`) / **要件2 (byte-identical default guard, HARD 非交渉)** = enabler wiring (:1120/:1135 per-world k) は **all-worlds-phase-0 = 現 reset_to_phase(0) 挙動に default**、B⑨a′ regression scope に「contract 変更 (widened 署名 + all-zeros default)」を明示追加し env-core ⑨a′ 25/81 + ⑩ + ⑪ (flag-off/stub path) EXACT 再現を **gate item 化** (built-model geom + numeric 両方) / **要件3 (curriculum defer)** = 本 node は enabler wiring のみ (per-world 能力 + all-zeros default)、start-mix VALUES 供給 = D-2/trainer (item⑥ 整合)。**note: contract v1→v1.1 minor bump を env-core build plan §6 stub 契約 note に記録** (§運用4 confirmed-decision reflect、backward-compat) |
| ⑩ | C2-clip blast-radius は grep でなく built-model assert 要 | B⑨a′/MED9 の C2-clip default-off byte-unchanged 検証を **built-model geom introspection assert** (mjModel geom count/pos) に格上げ (grep は補助) |

### §10.3 build sequencing — Layer A front-load (%12 05:23 推奨)
- **Layer A byte-repro (DoD①、抽出忠実 guard、env-core 非依存) を先に GREEN 化**してから Layer B (DoD②③④⑥) を独立 cycle で。理由 (%12): (a) primary DoD + node 全体の先祖返り guard (b) env-core 非依存ゆえ Layer B の flag-flip/geometry surprise に blocked されない (c) 検証済 faithful-extraction anchor の上で 3-round churn した Layer B を組む。
- **coupling 評価 (flag-back 判断、%12 requested):** RouteExecutor module は Layer A (monolith substrate 経由) / Layer B (env-core substrate 経由) で **共有**だが harness/substrate は分離 (Layer A = `test_routeexec_byte_repro.py`、env-core 非依存)。∴ module skeleton は一度に書くが **verdict-GREEN は Layer A→B 順で分離可能** → coupling = module 共有のみ、**flag-back 不要 (現設計)**。module が自然一体 build になる兆候が出たら %12 に flag back。

### §10.4 design-gate 再走 (直交、code 前必須)
- **/geometric-design = table-void (Layer B 新 geometry element) に新 pass 必須** (%12)。base:1738-1769 の void (VOID slot Y + 2 X-fill box) が proven build_scene void (test:1055-1119) の mirror + monolith build_scene(gA=True) 実行成功済 → **reproduction-verify 見込み**だが gate は正規に。出力: reachability (grasp over void) + 断面図 (void slot vs **odd C1-clip@0.35 over-void / even@0.40 solid**、[[reference-clip-positions-vs-grasp-void-geometry]]) + clip-vs-void parity (RS71 §2) + 因果連鎖。
- **Layer A = 新 geometry 無ゆえ /geometric-design 対象外** (%12 confirm)。
- **/reward-design = 軽** (predicate 不変、§6)。**/force-design = skip 維持** (grip actuator params = base:1594-95 proven inherited、新規 force 設計無、§6)。**/pre-check = flag-flip 失敗モード** (grasp_actuation build artifact / void×clip interpenetration / grip cadence fidelity / all-16 exclusion 正当性) 検証。

### §10.5 5体 re-verify PROPOSE (full panel, delta-focus)
- **full panel 維持** (servo→flag-flip 材料変更、%12)。
- **PROPOSE focus = delta = Layer B** (grasp_actuation flag-flip 機構 + table-void×C1-clip parity + HIGH/MED 10項)。
- **Layer A 抽出 = full 5体#2 で検証済・不変** → PROPOSE に「**prior-verified, unchanged**」明記 (panel は読むが effort を delta に振る)。

## §11. /pre-check disposition (design-gate 2/2、verdict = WARN + SRG_PROBE_ONLY on grip-efficacy; verifier = 独立 skeptical sub-agent code-read)

**Claims 1(void parity)/4(floor)/5(clip-vs-void) = VERIFIED clean、6 cadence reproducible、2 byte-preserve は OFF-path のみ成立。5 findings fold (0 CRIT, 3 HIGH, 1 MED, 1 LOW)。build 非 BLOCK だが grip-efficacy verdict は measured landing control 前に bank 不可。**

### §11.1 build-critical (Issue 3, HIGH→CRIT-if-literal): per-world qd indexing + fancy-index exclusion
§運用28 reconcile: `:736-738` write は **既に per-world q** (`_arm_q_start[w]`/`_arm_qd_start[w]`:363-364; cable FREE root ゆえ 7q≠6qd for w≥1、:358 comment)。verifier の「flat [6,10,20,24]=world0 only」framing は :738 に不正確 (既 per-world) だが **substance 正**:
- **exclusion = fancy-index**: :738 の contiguous `phys_jq[jq0:jq0+28]` → `phys_jq[jq0 + _ARM_OVERWRITE_IDX]` (`_ARM_OVERWRITE_IDX={0-5,14-19}`=arm-only 12 coords、gripper {6-13,20-27}=16 coords 除外→actuator 駆動)。gripper は 28-slice 内 interleaved (arm-L[0:14]/arm-R[14:28]) ゆえ **slice-shrink 不可、fancy-index 必須**。
- **grip cmd = per-world qd**: `control.joint_target_pos[_arm_qd_start[w] + driver_local]` (drivers [6,10,20,24] を per-world qd offset で; flat 不可)。
- assert: 各 world の 4 drivers が POSITION-mode joint に着地 (post-finalize built-model)。**§10.1 の「全16 除外」を per-world fancy-index に具体化。**

### §11.2 grip-efficacy SRG (Issue 1, HIGH + ⭐SRG_PROBE_ONLY)
grip retention = fidelity-bound: env-core `RL_SIM_SUBSTEPS=4` vs oracle `SIM_SUBSTEPS=10` = **2.5× coarser** per-substep dt (stiff neg-PAD_SOLREF/condim6 contact grasp); monolith grasp runner 自身 (test:3047-3054) が **MECHANISM-ONLY bank** — grip magnitude/engagement/retention-through-lift は GPU HARD gate に defer。→ **grip-retention verdict は 10-substep monolith から bank 不可**。DoD④/B③ に **measured 4-substep grip-retention landing control (probe)** を green 化してから grip verdict bank (SRG_PROBE_ONLY = 1 labeled scoping probe 可、verdict-bind/self-iterate 不可)。substep 4→10 decouple (grip-phase のみ 10) = Rs-level substrate 判断 (現 4 維持+実測)。⚠ Layer B は既 non-conservative 実測ゆえ整合、**landing-control 明示化が delta**。

### §11.3 predicate re-validation under void (Issue 2, HIGH)
grasp_actuation=True の void は cable rest-Z under C1 を変える (cable center = CLIP1_Y=0.150 = void center:1520、middle ~120mm が void span unsupported) → C1-retention (z<0.840 `_c1_retention_m`:762-778) / seat metrics (:780-791) / `_cable_z_rest`:402 が void-substrate で異なる。⚠ **§運用28 reconcile**: monolith 0.716 は **void 上** (build_scene gA=True, test:3715) + **同 predicate** で earn ゆえ predicate は **void-calibrated**; env-core SOLID ⑨a′ 25/81 は **offline proxy = 別 substrate**。→ fold: 「Layer-B re-BASELINE」を sharpen = **void substrate = PROVEN route substrate (0.716)**、B⑨a′(solid) は **OFF-path のみ** guard。Layer B が void predicate を live 実測、Layer A byte-repro が monolith void route との一致で担保。「env-core solid-table 認定が void に transfer」を assume しない。

### §11.4 contact-path divergence (Issue 4, MED)
monolith grasp runner = `solver.step(...,None,SIM_DT)` **NO model.collide** (disable_contacts, test:1819/1834-35); env-core `_physics_step_all` = **collide+contacts** every substep (:374-77)。banked pad-cable contact (condim6/neg solref) は None-path 由来 → collide+contacts path が同 resolution 再現かは未検証。→ Layer B validation: SolverMuJoCo contact source を両 pattern で confirm (grip parity 依存)。

### §11.5 write-site audit (Issue 5, LOW)
reset `:617` が gripper を `FINGER_OPEN_POS=0.04` (Franka 40mm) に pin (actuator OPEN = `GRIPPER_DRIVER_OPEN_RAD=0.0` rad)。one-shot open は harmless だが **全 28-slice `phys_jq` write site (:389/:617/:738) を audit** し live-grip window 中に gripper re-pin しないこと (finding⑦ 一般化、exclusion 一貫性)。

### §11.6 built-model assert (item⑩ + ⭐%12 05:49 基準)
**table shape box count == EXACTLY 4** (2 Y-solid + 2 X-fill)。**5 = solid single-box 残存 = void 充填 = grasp 機構破壊の兆候** (%12)。+ 各 box `(hx,hy,cx,cy)` を §10.4 式値 (slot_Y[0.090,0.210]/slot_X[0.234,0.366]) と照合 (mjModel geom introspection)。C1 clip(float z=0.829) vs table box(z_top=0.80) 非重複 assert も。grep でなく built-model (item⑩)。

### verdict handling
**WARN (0 CRIT)** → build 非 BLOCK、ただし Rs approval 要 (skill Step4)。**SRG_PROBE_ONLY (grip-efficacy)** → grip-retention verdict は measured landing control 前に bank 不可。全 finding fold 可 (mechanism 不変、redesign 不要)。→ 5体 re-verify PROPOSE に §11 findings 反映 (%12: no re-checkpoint) → RULE-CHECK → build (Layer A front-load; grip verdict は §11.2 landing-control gate 越え後)。pre-check log = `logs/pre-check-log.jsonl`。

---

*%11 COORD (w2:p3) 起草 2026-07-07 / rev v1.1 (00:32) / rev v1.2 (01:22 pre-check 2 CRIT: 2-layer DoD + gripper-servo + HIGH4/MED5/MED6) / **rev v1.3 (re-pre-check BLOCK fold: CRIT1 自前 IK stack verbatim copy 確定 [1-ULP monkeypatch、import-reuse 撤回] + Issue2 explicit-solver 不採用 + Issue3 Layer A 実行モデル [run_route self-driving / step_target facade] + Issue4 env-core ⑨a′ 再regression [B⑨a′] + Issue5 citation :724-727 + Issue6 reset cable-state+_per_world_fk_jq + Issue7 A② bank-vs-monolith spot-check)**。PAPER-ONLY / INVARIANTS 不触 / locked runner 不触 (global mutate 禁止) / task_config 不触。**Layer A (verdict+trajectory byte-identity, 自前 IK stack) = 先祖返り guard / Layer B = substrate-transfer 実測 (非保守)**。**/pre-check 3 round: round1 BLOCK (substrate mismatch→2-layer) → round2 BLOCK (IK 1-ULP→自前 copy) → round3 WARN (内部整合 2 HIGH fold: line76/23 import-reuse 矛盾撤去 + transitive-closure manifest + two-copy drift gate; 0 CRIT = 収束)**。→ %12 re-checkpoint PASS → **5体 [VERIFY] = FAIL (4 CRIT/HIGH, NHA=CHANGE_JUSTIFIED)** → **v1.4 完成**: governance-independent (CRIT1/2/4 + MED5-8,10-12) + **env-core-source (CRIT3/MED9) = ⭐Rs 決定 A (cross-node 3 箇所 flag-gate default-off、`bad0d25204`) で fold** + /force-design skip (力 inherited)。→ re-pre-check = BLOCK (1 CRIT servo-kinematic + 1 HIGH ee_tgt-GPU + 2 MED) → **v1.5 fold**: servo 機構訂正 (`_ARM_OVERWRITE_IDX` gripper 除外 + PD schedule、旧「:731-742 不編集」= kinematic-close 抵触ゆえ撤回) + ee_tgt HARD L∞=0 を CPU-det phase 限定 (C2 re-grasp argmin は GPU 由来) + grip-hold viability 軸 (%12) + stale text 訂正。→ **次 = full 5体 再走** (%12 02:37、FAIL 復帰 + env-source 新 surface) → **full 5体#2 = FAIL (LOAD-BEARING CRIT: env-core grasp_actuation 欠落 → v1.5 servo inert)** → **rev v1.6 (servo-scope escalation DISPOSITION Rs=A `9b9a41604c` + %12 plan-ACK 05:23): v1.5 drive-loop servo 撤去 → `grasp_actuation=True` flag-flip [proven base:1586-1740 build_scene mirror, route:339 kwarg default-off, 4th flag] = 3 findings 同時解消 [inert-servo/CC4#5/finding#5 全16除外] + full 5体#2 HIGH/MED 10項 fold [§10.2] + %12 sequencing [Layer A byte-repro front-load] + design-gate /geometric-design table-void 新 pass [§10.4] + 5体 re-verify delta=Layer B [§10.5]。⭐§10.1 が v1.6 grip 機構 governs (§2b/§9 servo inline SUPERSEDED)**。build 非進行。*
