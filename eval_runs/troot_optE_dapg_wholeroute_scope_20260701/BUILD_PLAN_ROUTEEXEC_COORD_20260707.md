# P2 部品② route-executor — BUILD 計画 (COORD %11 起草, %12 checkpoint 用) — 2026-07-07

**node:** `T-ROOT-optE-route-dapg-C1C2-P2-routeexec` (state.md 済, IN_PROGRESS, 1:1 bind %11/w2:p3) · **L:** L3 (charter §3 自動昇格 confirmed, §1 で再導出 concur)
**charter-giver:** %12 RS-TECH-LEAD (w2:p4) · **task-start SHA:** `f0bd54992c` (5体 [VERIFY] git diff 起点)
**status:** PAPER-ONLY / 0-build / 0-commit-of-code (本 doc = charter INPUT、[DESIGN-GATE]+5体 [VERIFY] への提出物)
**rev:** v1.1 (%12 checkpoint 00:32 fold: fn-range 訂正 3692-7475 / **canonical 抽出 scope 3692-5765** [%12 CONCUR、当方 §運用10 catch] / per-closure 3-way 分類 / namesake 全列挙 / state-bank = 6 coarse G)

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
| shared IK helper | `test_newton_clip_routing.py:1958` `def ik_move_both` | route の move primitive = **共有 module-level helper** (monolith 内部でない、再利用可) |
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
| `ik_move_both`:1958 / `_set_gripper_target` / `get_ee_positions` / `solve_ik_dual` (module-level) | ❌ **import 再利用** (不触) | 既存 module 参照 |
| predicate (`c2_seated_honest`:5580 wall-excluded / `c1_final`:5586) | ❌ **env-core owns** (G6 strict_v2 mirror v1.5f) | reference oracle 側で byte-repro 照合 |
| **`_b` closures 24個 (≥5766)**: `_close_b`:6501 / `_halfclamp_b`:6511 (しごき) / `_feed_claw_cable_load_N`:6548 / `_gap_mm_from_drv`:6469 / `_span_sag_mm`:6589 / `_do_step_b`:6480 等 + DH-F1-R-DESCEND:6168 + STEP13_REGRASP/CLIP_DELTAH block | ⛔ **dead-under-canonical** | reference-oracle-only (抽出せず、loud 記録; %12 finding(3) の closure は dead 側) |

**closure 会計 (§運用28、%12「25」と当方「27」reconcile):** canonical ≤5765 = **27 closures** (exact grep `awk '/^ +def /' 3692-5765`)。うち **抽出 = 7** (target/IK) / **residual = 20** = measurement 15 + video 2 (`_world_to_pixel`/`_cap`) + recorder/naming 2 (`_ph`/`_gn`) + DR-passthrough 1 (`_inject_detour`) = 15+2+2+1 = 20 (7+20 = 27 ✓)。%12「25」との差 2 = pure-render `_world_to_pixel`:4024 + `_cap`:4045 (route-closure でないゆえ %12 非計上と解す — 分類は両者 RESIDUAL で不変)。dead ≥5766 = **24** (%12 一致)。⇒ **抽出対象 = 27 closure 中 7 のみ + inline orchestration** = LOC は canonical span より遥かに小。

**新規/変更 file (core module ≤800L、byte-repro test 分離):**
| file | 内容 | 行 (見込) | reuse |
|---|---|---|---|
| **新規** `thread_isaac_lab/envs/route_executor.py` | `class RouteExecutor(rc.RouteInterfaceV1)` = step_target/reset_to_phase(6 coarse G)/grip scheduler/recorded-replay mode。**抽出 = 7 closure (target/IK) + inline orchestration**; ik_move_both/geom は import 再利用 | ~400-650 | canonical route-logic 抽出 (7/27 closure + inline) |
| **変更** `route_env_config.py` | C2 groove block (ROUTE_C2_XY / ROUTE_C2_GROOVE_Z) — 既存 ROUTE_* block (`a6cbc148ab`) に追加、meta verbatim+provenance | ~40-60 | env-core ROUTE_* pattern |
| **変更** `newton_route_env.py` | `self._route` = `NominalRouteStub` → `RouteExecutor` 差し替え (interface 不変、`:309`/`:1101`/`:1120`) + reset_to_phase 実配線 | ~40-80 | interface 既定 (RouteInterfaceV1) |
| **変更** scene builder (`newton_skill_env_base` C2 add) | C2 target clip 建設 (env-core=C1 only, skill_base:1826 pattern) | ~50-100 | C1 pattern mirror |
| **新規 (test)** `thread_isaac_lab/scripts/test_routeexec_byte_repro.py` | byte-repro regression harness (§4): locked oracle ↔ RouteExecutor 81-grid strict_v2 EXACT | ~150-250 | w0e_81rerun harness + test_route_geometry_sync pattern |

**⚠ LOC 見込 (core module ~400-650 + 変更 ~130-240 + test ~150-250 ≈ 680-1140 total):** canonical 2073L の大半 (20/27 closure) が harness-residual ゆえ抽出 core は縮小 (spec §7:102 の「300-800 touched」と整合)。**core module (route_executor.py) を ≤800 に収め、byte-repro harness は test file に分離**して L3 chain 単位を保つ。超過時は %12 checkpoint で split 要否判断 (env-core precedent: 1329L を単一 L3 chain で承認)。

---

## §3. DoD (charter §1 = node state.md:6-15、byte-repro = 全項前提)

| # | 項目 | bar / 判定 | env-core からの引き上げ |
|---|---|---|---|
| ① | **byte-repro (PRIMARY)** | 抽出 route で canonical 81-grid → strict_v2 **58/81 EXACT** (per-cell、cuda:0 canonical、FON_V1 pin) | ⑨a′ recorded-state proxy 25/81 → **live 58/81** |
| ② | **⑦ handover-fidelity** | `reset_to_phase(k)` 復元 state の qpos/qvel L∞ ≤ **1mm / 1mm·s⁻¹** (env-core stub は no-op :1120) | 実 state-bank 実装 |
| ③ | **⑨b online-numerator** | residual≡0 × 81 live → 58/81 (live earned-clock + contact + physics; recorded-replay で代替不可) | env-core LOUD-CARRY discharge |
| ④ | **⑥ 6-phase full-fire live** | 実 grip で cable carried → G2-G6 live fire (env-core = fingers-open geometric-proxy) | premise-correction discharge |
| ⑤ | **58/81 wall/spacer exact predicate** | mjModel geom introspection: center-dist≤3.5mm proxy → **wall-dist≤0.5mm spacer-excluded** (`c2_seated_honest`:~5580 と一致) | env-core 25/81 proxy の構造 discharge |
| ⑥ | **C2-seating 動画 gate** | 実 C2 groove scene で C2 着座を §運用14 CC frame-check + video-analyst + Rs verdict (Rs 約束済) | env-core = C2 honest-defer |
| ⑦ | **CABLE_XY_OFFSET per-cell wiring** | 実 route が per-cell offset を消費 (DR/⑨b 前提; env-core = INIT_XY_NOISE のみ) | offset cell 実配線 |
| ⑧ | **⑬ enabler のみ** | recorded-target-replay stub upgrade + **C1-escape non-vacuous cell ≥1 供給** (pre-snapdown 36/81-escape grid)。**⑬-VERDICT (residual≠0→G6==strict_v2) = D-2 trainer 段 defer** | enabler owns、VERDICT defer |

**分子完全性 (§運用29):** 分子 conjoin = **strict_v2 (C1-retention leg ∧ C2-seat leg 両方)**。cover しない leg = **trainer 段 policy 学習成果** (本 node scope 外、明示)。SR claim を route-executor で出さない (SOMA:717、over-claim 禁止)。

---

## §4. byte-repro regression harness 設計 (D-1=C の一次 guard、先祖返り防止)

**目的:** faithful 抽出の挙動 delta ゼロを機械証明。二重 SSOT (locked oracle + 新 module) の drift を byte-repro が捕捉。

**手順:**
1. **reference leg (locked, 不触):** `_run_mujoco_grasp_route`:3692 を canonical 81-grid (w0e_81rerun_snapdown harness) × cuda:0 × W0E_F1B_SNAPDOWN=1 で走らせ、per-cell strict_v2 verdict = **golden 58/81** (banked provenance `w0e_81rerun_snapdown_0537`)。
2. **module leg (新):** `RouteExecutor` を env-core (residual≡0 online) 経由で同一 81-grid × 同一 device/pin で走らせ、per-cell strict_v2。
3. **assert:** 両 leg の per-cell verdict が **81/81 EXACT 一致** (58 PASS + 23 FAIL の cell 集合が完全一致)。**≥1 cell でも不一致 = 抽出 infidelity = build FAIL (先祖返り、fix-first)**。
4. **namesake guard:** reference は production `_run_mujoco_grasp_route`:3692 のみ (legacy `_run_mujoco_grasp_episode`:3036 / `_grasp_engage_episode`:3230 と混同禁止、[[reference-test-newton-legacy-vs-production-route-namesake-functions]])。
5. **device pin:** byte-repro 判定 = **cuda:0 canonical のみ** (route device-fragile、[[project-canonical-route-device-fragile-cpu-vs-cuda]]; cpu = read-only proof、判定に使わない)。

**conservatism 方向 (GROVE v1.1):** byte-repro EXACT-match は**問うている量 (抽出忠実性) について確定的** — 一致すれば挙動同一 (conservative)、不一致は確定的 infidelity。GPU#562 非決定性が残余 risk → **N 回 (≥3) 再走で per-cell verdict 安定性**も確認 (verdict が非決定的に揺れる cell は別途 flag)。

---

## §5. stub 契約 v1 実装方針 (env-core interface `rc.RouteInterfaceV1` を実装)

env-core `NominalRouteStub`:178 が実装する契約を `RouteExecutor` が実装 (interface 不変、差し替えのみ):

```
class RouteExecutor(rc.RouteInterfaceV1):
    reset_to_phase(k) -> None
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

**grip schedule single-source (CC5-2):** is_dual_grip window + arm-role (reaching=full σ / gripping=σ-cap) は **base grip-schedule から導出** (env 再導出 phase→window table 禁止 = env-core NEW-D と同一 deterministic source、boundary mislabel→drop 防止)。

---

## §6. [DESIGN-GATE] (直交, code 前必須) — 実行予定

- **`/geometric-design`** (C2 groove scene): C2 clip 配置 (ROUTE_C2_XY canonical (0.40,0.000) 間隔倍化 CLIP2_Y=0)、C2 groove geometry (walls/spacer split for wall-dist≤0.5mm)、C1↔C2 間隔と cable span (92.4mm) の幾何整合、C2-over-solid vs C1-over-void 床 parity ([[reference-clip-positions-vs-grasp-void-geometry]])。6 ステップ出力 (実測・制約・断面図・トレード・感度・因果連鎖)。
- **`/reward-design`** (軽 — route/predicate 不変): route-executor は G1-G6 predicate を**変更しない** (env-core spec v1.5f が SSOT)。到達可能性は **live route で predicate が earn される**ことの確認のみ (predicate code 不変ゆえ artifacts v1.3 の再 discharge は差分のみ)。
- **`/pre-check`**: 抽出失敗モード (byte-repro drift / state-bank fidelity / grip timing / C2 scene artifact) を Claude sub-agent で検証。BLOCK なら redesign→re-run。
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

1. **抽出粒度 (per-closure map、%12 checkpoint で確定):** module-level helper (ik_move_both/geom) の reuse-import = **%12 承認**。fn-local closure は import 不可 → **§2 の 27-closure per-closure 分類が granularity の実体** (抽出 7 [target/IK] / residual 20 / dead-≥5766 24)。抽出 7 closure は `RouteExecutor` の method 化 (self に fn-local state を保持) = closure→method 変換が抽出の core 難度。inline target (W0-e guarded_cx / seat k/8 / ANTI-REVERT) は copy 不可避 → byte-repro が drift guard。**5体で per-closure 分類 + method 化の忠実性を精査。**
2. **state-bank 粒度 = ✅ RESOLVED (6 coarse G、%12 CONCUR 00:32):** `reset_to_phase(k)` の k = coarse G semantics (spec:29 curriculum start-mix 消費者に一致、15-fine は消費者無=YAGNI over-provision)。内部 fine bank は faithful/安価なら実装可だが expose は coarse G。5体 [VERIFY] で残置。
3. **byte-repro tolerance:** strict_v2 verdict は boolean per-cell ゆえ EXACT-match が自然。ただし GPU#562 非決定で verdict-flip する境界 cell の扱い (§4 手順5) = **N≥3 再走で安定 cell のみ golden、非安定 cell は flag+carry**。bar 緩めでなく非決定性の honest 会計。
4. **C2 groove scene の 3mm proxy 非保守 (charter §8):** 剛体 clip 非保守 carry を C2 でも承継 (spec §8)。実機前に再訪 (over-claim 禁止)。
5. **recorded-target-replay の horizon cadence:** monolith 7709 frame → env horizon 900 の resample (env-core :192 で既配線、cadence 整合を byte-repro で確認)。

---

## §9. risks / conservatism carries (charter §8 承継)

- **Rs-LOCKED file 関与 = 最大 risk (先祖返り class):** byte-repro regression = 一次 guard。抽出中に「挙動を変える」判断が出たら **STOP → BLOCKED_FOR_USER (Rs)** (§1 high-care)。
- **byte-repro の device 依存:** cuda:0 canonical のみで判定 (cpu = read-only proof、[[project-canonical-route-device-fragile-cpu-vs-cuda]])。
- **namesake hazard (%12 訂正、全列挙 guard):** production `_run_mujoco_grasp_route`:3692 のみ cite。混同禁止の全 legacy 列挙 = `do_p1_grasp`:2227 / `run_episode`:2746 / `_run_mujoco_grasp_episode`:3036 / **`_run_mujoco_grasp_engage_episode`:3230** (旧 doc の `_grasp_engage_episode` は `_run_mujoco_` prefix 欠 = 訂正) / `_run_mujoco_episode`:7478。byte-repro harness は :3692 を明示 cite (C 案で二重 SSOT ゆえ特に重要、[[reference-test-newton-legacy-vs-production-route-namesake-functions]])。
- **state-bank fidelity (⑦):** qvel は live state から取得 (recorder に qvel 無、spec:29)。L∞≤1mm/1mm·s⁻¹ を DoD② で機械証明。
- **oracle/OG/trainer は本 node 非該当:** SR/学習成果 claim を route-executor では出さない (SOMA:717、trainer/campaign 段、over-claim 禁止)。
- **⑬-VERDICT defer (D-2):** route-executor は ⑬ enabler のみ。residual≠0 VERDICT は trainer 段実 policy (合成摂動の representativeness risk 回避、Rs 23:5x)。

---

*%11 COORD (w2:p3) 起草 2026-07-07 / rev v1.1 (%12 checkpoint 00:32 fold: fn-range + canonical 抽出 3692-5765 + per-closure 3-way + namesake + state-bank 6-coarse-G)。PAPER-ONLY / INVARIANTS 不触 / locked runner 不触 / task_config 不触。byte-repro = 全 DoD 前提。→ %12 re-checkpoint 提出。*
