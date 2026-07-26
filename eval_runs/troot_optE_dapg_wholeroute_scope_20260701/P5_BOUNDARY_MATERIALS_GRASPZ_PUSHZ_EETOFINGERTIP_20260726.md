# 境界材料 — `GRASP_Z` / `PUSH_Z` / `EE_TO_FINGERTIP`（要求事実の列挙のみ）

> ⛔⛔ **2026-07-26: 本書は 5 点訂正された（原因側 = p5 自身）。訂正版 = `P5_BOUNDARY_MATERIALS_CORRECTION_20260726.md`（stable ID `P5-BOUNDARY-MATERIALS-CORRECTION-20260726-001`）を先に読むこと。**
> 契機 = pN RETURN `MSG-PN-P5-FINGERTIP-MATERIALS-RETURN-20260726-001`（B1-B5）。**5 件すべて p5 が独立実測で CONFIRM**。
> **B1** 行番号・引用は **as-read working tree**（banked でない）。`changed=[newton_grip_env.py, newton_approach_cable_mujoco_env.py, step_table.py, test_newton_clip_routing.py, newton_routing_utils.py]`・`untracked=[harness/scripts/predict_training.py]`（**commit tree に不在**）。⚠`newton_grip_env.py` の引用は banked では **一律 −5 行**（例: `tip[2] -=` `:751/:757` → **`:746/:752`**）。⭐banked に列挙漏れの `compute_clamp_pos` 呼出 **`:1610/:1617`** が存在。
> **B2** 件数は working-tree 由来で **banked と 10 件相違**（`test_diagonal_reach` 13／`test_motion_sequence_dry_run` 11／`collect_expert_demos` 3／`demo_aerial_regrasp` 1 は記載漏れ 等）。exact query と役割分類は訂正版 §2。
> **B3** 下記 `全 skill 横断（下流全部）` = **RETRACTED**（本書 §2/§3/§4 と矛盾）。⭐**「全 skill 共通でない」結論は保持**。
> **B4** 「Z-Check が finger body z を直読 ⇒ 観測移行の live 先例」= **格下げ / UNVERIFIED**（SSOT の pad は `[9,13]`・読み取りは `+7/+8`＝**stale/mismatch 候補**）。
> **B5** 「物理接触面 = f1ext 爪先」= **UNMEASURED**（banked `route_executor.py:2436-2440` は f1ext+f2ext の sandwich・f1ext-only は false-FAIL 実績）。
> ⭐ **owner / 値 / 方式の非選択と CLOSED gates は不変。** 原文は履歴として残す（rewrite しない）。

**stable ID:** `P5-BOUNDARY-MATERIALS-GRASPZ-PUSHZ-EETOFINGERTIP-20260726-001`
**著者:** SKILL-DETAIL-DESIGN (`w2:p5`)。**発行:** 2026-07-26T17:32:57+09:00（shell 実測）。
**依頼元:** pN relay `MSG-PN-P5-FINGERTIP-BOUNDARY-MATERIALS-20260726-001`（p17 scope response = T1 skill identity/count・T2 frame/unit・T3 fixed-vs-composition-vs-observation のみ／**定数値・geometric/reward gate・arm-target・landing を p17 単独で決めない**／**B/C owner はなお UNCONFIRMED/HOLD**）。
⛔ **本書は材料のみ。owner / 値 / 方式を選ばない。** p11 側材料と合流後に p17 が taxonomy を分類する。
⛔ source / `[CHANGE]` / 実装 / RUN / verify / status / gate flip = **CLOSED**（本書は records/design material）。

**列挙の規律:** 全て on-disk 直読。閉じたクエリは `.git` と worktree 複製（`.codex/worktrees/`・`.claude/worktrees/`）と `*.pre_3c_backup` を除外し、**live code（`*.py`）** を対象にした。⚠ `eval_runs/` 配下の `*_pre_*`・`BASELINE_*`・`RECOVERED_*`・`*_deleted.py` 等は **凍結された歴史 snapshot** であり live consumer に数えない（数のみ後述）。

---

## 0. 3 定数の定義（source pin）

| 定数 | 定義 | 値 |
|---|---|---|
| `EE_TO_FINGERTIP` | `task_config.py:78` | `0.220` — 自己ラベル「FRANKA panda_hand->fingertip [m]」／`:84`「220mm, Franka value; **re-derive S6**」／`:324`「(0.220) is the **Franka/legacy**」 |
| `GRASP_Z` | `task_config.py:93` = `TABLE_HEIGHT + CLIP_BASE_HEIGHT + EE_TO_FINGERTIP` | `1.025` — 注記「fingertip at clip base top (= cable bottom)」 |
| `PUSH_Z` | `task_config.py:95` = 同式 | `1.025` — 注記「same as `GRASP_Z`」 |

⭐ **構造事実**: `GRASP_Z`/`PUSH_Z` は `EE_TO_FINGERTIP` の**派生**であり独立変数ではない（`:93`/`:95`）。⇒ 3 定数は 1 個の測定面仮定を共有する。
**対照（コ実測・同 file）**: `EE_TO_PINCH_CLOSED=0.2548428289592266`（`:320`「wrist_3 -> pinch_mid drop」）／`EE_TO_PINCH_TIP_CLOSED=0.27574726696`（`:321`「pad TIP drop・コ f1ext claw tip」）／`EE_TO_PINCH_OPEN=0.26092`（`:326`「pinch_mid drop, OPEN gripper」）。

---

## 1. `EE_TO_FINGERTIP`

### (1) 実 consumer / skill と source pin

| consumer | 用途 | skill 帰属 |
|---|---|---|
| `task_config.py:93` / `:95` | `GRASP_Z` / `PUSH_Z` を導出 | ~~**全 skill 横断**（下流全部）~~ ⚠**RETRACTED（B3）** → 派生先は `GRASP_Z`/`PUSH_Z` の 2 定数。consumer は §2/§3 の集合であり ⛔**approach(mujoco)・route_c1_c2 は非消費**（訂正版 §3） |
| `envs/newton_skill_env_base.py:902` `clamp_pos = ee_pos + quat_rotate(ee_quat, [0,0,+EE_TO_FINGERTIP])`（`:904` 同式の local offset） | **success 述語の測定点**（`compute_clamp_pos`） | **acquire-grasp**（`newton_grip_env.py:1163`/`:1169` → 距離 `:1174-1176` → 判定 `:1230`/`:1236`） |
| `envs/newton_grip_env.py:751` / `:757` `tip[2] -= EE_TO_FINGERTIP` | cable 目標分節の選択（最近傍探索の query 点） | **acquire-grasp**（obs 用の target seg） |
| `configs/mpc_config_ic.py:146` | 「approach: 91mm descend（`LIFT_Z=1.120` → `GROOVE_CENTER_Z=0.809 - EE_TO_FINGERTIP`）」 | **insert**（IC） |
| `envs/newton_grip_env.py:110` | import | acquire-grasp |
| scripts（probe / dry-run / demo 生成 / 計測）| `test_newton_clip_routing.py`×12・`test_newton_clip_routing_sdf_plain.py`×11・`generate_demos_mppi_m3_ar.py`×6・`m4_phase0_verify_ee_clamp.py`×5・`test_motion_sequence_dry_run.py`×3・`test_grip_modes.py`×3・`measure_finger_extent.py`×3・`demo_aerial_regrasp.py`×3・`build_aerial_regrasp_precondition.py`×3・`test_newton_20clip_reachability.py`×2・`plot_fingertip_waypoints.py`×2・`dry_run_approach_cable.py`×2・`eval_skill.py`×1・`harness/scripts/predict_training.py`×2・`eval_runs/…/arm_control_measurement_harness.py`×5 | 横断（多くは検証・記録側） |

（凍結 snapshot = `eval_runs/` 配下 15 file・live に数えない。）

### (2) 必要 measurement surface
**要求されている面 = 「cable に接触する点」の世界位置**。現状の実装が置いている面 = **wrist_3 から `0.220` 下の nominal 点**（`:902`）。⚠ ~~物理接触が起きる面は **コ f1ext 爪先**~~ ⚠**UNMEASURED（B5）**〔実際の接触 geom は未測定。banked `route_executor.py:2436-2440` は retention を **f1ext(bottom)+f2ext(top) の sandwich**＋横 footprint で定義し **f1ext-only の旧 gate は false-FAIL 実績**（`:2438`）⇒ 単一 geom を接触面と断定できない。以下の asset 幾何事実のみ保持〕**コ f1ext 爪先**（asset `2f85_koshape.xml:116` `right_pad_f1ext`・実測 `0.27574726696`）であり、両者は **55.7mm** 離れる。
⭐ `dist_pos` は **`clamp_pos`（0.220 点）↔ 物理 cable body** で測る（`newton_grip_env.py:1174-1176` `find_nearest_cable_point(cable_pos, clamp_r_pos, …)`・query 点は第 2 引数 = `newton_skill_env_base.py:845`）⇒ **offset 差は success 距離に残り、目標側と相殺しない**。

### (3) frame / unit
- **unit** = スカラ長 `[m]`。
- ⚠⚠ **同一定数が 2 つの frame で適用されている**:
  - `newton_skill_env_base.py:902` = **EE frame の local +Z を quat で回して加算**（`quat_rotate(ee_quat,[0,0,+E])`）⇒ 姿勢依存。
  - `newton_grip_env.py:751`/`:757` = **world −Z にのみ減算**（`tip[2] -= E`・x,y 不変）⇒ 姿勢非依存。
- ⇒ 両者は **特定姿勢でのみ一致**する。**どの姿勢で一致するか／nominal 把持姿勢での乖離量は本書では未測定**（H-4 を 3 参照点で測る p11 の計器が該当）。

### (4) 要求事実（共通必要 / skill 別分割可 / 観測量へ移行可）
- **共通である必要（事実）**: `GRASP_Z`/`PUSH_Z` を導出する唯一の項（`:93`/`:95`）であり、`step_table.py`→`scripted_skills.py`→env の連鎖に単一値で流れる。⇒ **分割するなら派生 2 定数と step 表側に per-skill の受け皿が要る**。
- **skill 別に分けられる（事実 = 既に分岐している）**: `insert` は `GROOVE_CENTER_Z - EE_TO_FINGERTIP` を使う（`mpc_config_ic.py:146`）が、`approach`(mujoco) は **本定数を使わずコ実測へ移行済**（§4 参照）。⇒ **skill 別の面は既に併存**。
- **観測量へ移せる** ⚠**（B4 で格下げ: 「同 repo に live 先例」を RETRACT ⇒ 残る根拠は asset に pad body が実在することのみ。`+7/+8` が pad/finger かは **UNVERIFIED**〔SSOT の pad = `task_config.py:37/48` の `[9,13]`〕⇒ **stale/mismatch 候補**であり対等な 2 規約ではない。訂正版 §4）**: `2f85_koshape.xml` に **`left_pad`/`right_pad` は実 body**（`:154`/`:107`）、爪先は pad 上の geom（`:116` `f1ext`・local `pos="0 -0.0026 0.0382"`）。live 先例 = **Z-Check が finger body z を定数なしで直読**（`test_newton_clip_routing.py:468-470` `body_q[bs+7][2]` / `body_q[bs+8][2]`・同 `:466` は hand z）／**grip env も finger body を読む**（`newton_grip_env.py:649-663` `_finger_physics_ids`・`task_config.py:48` `FINGER_LOCAL = GRIPPER_PAD_BODY_IDX # [9,13] (BODY-space finger-pos reads)`）。
  ⚠ **未解決事実**: 「finger body」の index 規約が **2 つ併存**（Z-Check は `+7`/`+8`・grip env は `FINGER_LOCAL=[9,13]`）。／asset の `<site name="pinch">`（`:79`）は site であり、**Newton が site pose を露出するかは未検証**（pad **body** は読めている）。

---

## 2. `GRASP_Z`

### (1) 実 consumer / skill と source pin

| consumer | 用途 | skill 帰属 |
|---|---|---|
| `envs/newton_grip_env.py:118` import・`:147` `GRIP_Z = GRASP_Z + CABLE_RADIUS`（注記「fingertip at cable center Z (0.809)」・`:146`） | 把持高さの基準 | **acquire-grasp** |
| `configs/mpc_config_grip.py:110` | 「Grip P0 precondition already positions arms at `GRASP_Z`」 | acquire-grasp（P0） |
| `envs/route_executor.py:2450` | ⭐**逐語「`GRASP_Z`/`PUSH_Z` (task_config) are the LEGACY P1-P4 path, NOT used by `route_c1_c2`」** ⇒ route の下降目標は `GROOVE_CENTER_Z + ee_off`（動的） | **route（C1→C2）＝本定数を使わない** |
| `envs/newton_approach_cable_mujoco_env.py:197` | ⭐**逐語「the koshape OPEN claw bottom reaches the cable centerline (NOT 40mm into the table via the stale Franka `GRASP_Z=1.025`). pre-check ISSUE-3」** ⇒ 代替 = `EE_Z_FLOOR_KO = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS + EE_TO_PINCH_OPEN ≈ 1.06992`（`:200`） | **approach（mujoco）＝コ実測へ移行済** |
| `scripts/newton_routing_utils.py` ×5 | route/scripted の共有 utility | 横断 |
| scripts（probe/dry-run）| `test_motion_sequence_dry_run.py`×13・`test_clip_routing.py`×10・`build_aerial_regrasp_precondition.py`×8・`test_newton_clip_routing.py`×7・`test_diagonal_reach.py`×7・`sdf_plain`×6・`test_newton_dual_clip_routing.py`×5・`test_newton_20clip_reachability.py`×5・`test_grip_modes.py`×5・`test_arm_reachability.py`×5・`generate_demos_mppi_m3_ar.py`×4・`dry_run_approach_cable.py`×4・`dry_run_39step.py`×2・`collect_expert_demos.py`×2・`plot_fingertip_waypoints.py`×2・`harness/orchestrator/*`×5 | 横断 |

### (2) 必要 measurement surface
**「爪先が clip base 上面（= cable 底）に来る world Z」**（`:93` の注記どおり）。⚠ 現値は 0.220 面での nominal であり、**コ爪面では 40mm テーブル内**（`newton_approach_cable_mujoco_env.py:197` の code-resident 実測記述）。

### (3) frame / unit
**world frame の絶対 Z 高さ `[m]`**（`TABLE_HEIGHT + CLIP_BASE_HEIGHT + offset`）。⚠ `EE_TO_FINGERTIP`（frame 相対のスカラ offset）とは **frame 種別が異なる** — 同一値 `0.220` が「local offset」と「world 絶対高さの成分」の 2 役を負っている。

### (4) 要求事実
- **共通である必要（事実）**: `GRIP_Z`（`:147`）が本定数を基準に導出され、P0 precondition（`mpc_config_grip.py:110`）と同一面を仮定している ⇒ **P0 と success を同一面に保つ要求**が存在。
- **skill 別に分けられる（事実 = 既に 3 面が併存）**: ①acquire-grasp = `GRASP_Z`(0.220 系) ②approach(mujoco) = `EE_Z_FLOOR_KO`(コ `EE_TO_PINCH_OPEN`) ③route = `GROOVE_CENTER_Z + ee_off`（動的・`route_executor.py:2450`）。⇒ **「全 skill 共通」は現状の事実ではない**。
- **観測量へ移せる（事実）**: 目標高さは「爪先が cable 底に触る高さ」という**接触条件**であり、pad body（`2f85_koshape.xml:107`/`:154`）と cable body から**実行時に導出可能**（route が既に `GROOVE_CENTER_Z + ee_off` の動的形をとっている＝定数から動的量への移行先例）。

---

## 3. `PUSH_Z`

### (1) 実 consumer / skill と source pin

| consumer | 用途 | skill 帰属 |
|---|---|---|
| `skills/scripted_skills.py:39` import（`from task_config import …`・`:4`）・`:88` `return (x, y, PUSH_Z)` | scripted の押込目標 | **insert / scripted 系** |
| `skills/step_table.py:32` `from .scripted_skills import HOME_Z, PUSH_Z, …`・`:97` `return (cx, ly, PUSH_Z), (cx, ry, PUSH_Z)` | ⭐**canonical 43-step 表の両腕目標**（同一 Z を両腕へ） | **横断（step 表）** |
| `envs/newton_grip_env.py:128` import・`:435`/`:436` `ee_left/right = (CLIP1_X, CLIP1_Y ± GRIP_HALF_SPAN, PUSH_Z)` | unclamp P0 の腕配置 | **set_finger（unclamp）P0** |
| `envs/route_executor.py:2450` | 同上（**LEGACY 扱い・route は使わない**） | route = 非使用 |
| `scripts/newton_routing_utils.py` ×7 | 共有 utility | 横断 |
| scripts | `test_clip_routing.py`×11・`test_newton_clip_routing.py`×9・`sdf_plain`×8・`test_newton_dual_clip_routing.py`×6・`build_unclamp_precondition.py`×3 | 横断 |

### (2) 必要 measurement surface
`GRASP_Z` と**同一面**（`:95`「same as `GRASP_Z`」）＝「爪先が clip base 上面に来る world Z」。⚠ ただし用途は **押込（insert）** と **P0 配置** で、要求される面が把持と同一である必要があるかは本書では判定しない（要求事実のみ）。

### (3) frame / unit
**world frame 絶対 Z `[m]`**。⚠ `step_table.py:97` は **両腕に同一 Z** を返す ⇒ frame は world 共通・per-arm の区別を持たない。

### (4) 要求事実
- **共通である必要（事実）**: `step_table.py:97` が **両腕・全 clip に単一値**を配っている ⇒ per-skill / per-step 化には **step 表の signature 変更**が要る（現 `StepDef` は `target_left`/`target_right` に完全な 3 要素 tuple を持つので**受け皿は既にある**が、`_push_target`(`scripted_skills.py:88`) が単一定数を返す構造）。
- **skill 別に分けられる（事実）**: `route_executor.py:2450` が既に route 経路で**非使用**を宣言。⇒ 分離の先例あり。
- **観測量へ移せる（事実）**: 押込目標は「cable が溝に着座する深さ」であり、着座判定は既に **cable body 側の観測**で行われている（`newton_grip_env.py:1403-1406` `dist_pos < UNCLAMP_SEATED_POS_THRESH`・`GROOVE_TARGET_QUAT` 比較・`bodies_in_groove`）。⇒ 目標を定数 Z でなく着座条件から導出する余地が観測側に既に存在。

---

## 4. 横断して出た事実（分類に直接効く 4 点）

1. ⭐**3 定数は独立でない** — `GRASP_Z`/`PUSH_Z` は `EE_TO_FINGERTIP` の派生（`:93`/`:95`）。1 個の測定面仮定が 3 箇所に現れている。
2. ⭐⭐**「全 skill 共通」は現状の事実ではない** — 3 面が併存: acquire-grasp = 0.220 系／approach(mujoco) = コ `EE_TO_PINCH_OPEN`（`:197-200`・「stale Franka `GRASP_Z=1.025`」と code に明記）／route = 動的 `GROOVE_CENTER_Z + ee_off`（`route_executor.py:2450`「LEGACY … NOT used by `route_c1_c2`」）。
3. ~~⭐⭐**観測への移行は仮説でなく先例がある**~~ ⚠**RETRACTED（B4）** → 生の BODY-space index 読み取りが live code に在る事実は保持するが、それが pad/finger を観測している証拠はない（**UNVERIFIED**・訂正版 §4）。旧本文↓ — Z-Check は finger body z を定数なしで直読（`test_newton_clip_routing.py:468-470`）、grip env も finger body を読む（`_finger_physics_ids`）。pad は実 body（asset `:107`/`:154`）、爪先はその上の geom（`:116`）。
4. ⚠⚠**frame が 2 種混在** — `EE_TO_FINGERTIP` は EE-local 回転適用（`newton_skill_env_base.py:902`）と world −Z 直接減算（`newton_grip_env.py:751`/`:757`）の両方で使われ、**一致するのは特定姿勢のみ**。`GRASP_Z`/`PUSH_Z` は world 絶対高さ。

## 5. 未測定 / 未解決（捏造しない）

- `:902`（EE frame）と `:751`（world −Z）が **nominal 把持姿勢で一致するか・乖離量** = **未測定**（p11 の H-4 3 参照点測定が該当計器）。
- 「finger body」の index 規約が 2 つ併存（`+7`/`+8` vs `FINGER_LOCAL=[9,13]`）— **どちらが pad body かの照合は未実施**。
- asset `<site name="pinch">`（`:79`）を Newton が露出するか **未検証**（pad **body** は読めている）。
- 各 skill の要求面が**同一である必要があるか**（把持面 = 押込面 = 着座面か）= **要求事実の列挙に留め、判定しない**。

## 6. 非主張

- ⛔ **owner を選ばない**（B/C owner は UNCONFIRMED/HOLD のまま）。⛔ **値を選ばない**（0.220 / 0.2548 / 0.2757 / 0.26092 のいずれも推さない）。⛔ **方式を選ばない**（共通維持 / skill 別分割 / 観測移行のいずれも推さない）。
- ⛔ source / `[CHANGE]` / 実装 / RUN / verify / status / gate flip をしない。他 pane の record を編集しない。07-Design・04-Specs は CC read-only ゆえ触らない。
- p11 側材料（H-4 3 参照点）と合流後、**taxonomy 分類は p17**（T1/T2/T3 の範囲内）。
