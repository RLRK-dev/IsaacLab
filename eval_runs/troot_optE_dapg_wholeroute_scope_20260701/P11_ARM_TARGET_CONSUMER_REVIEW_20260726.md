# 腕側 consumer レビュー材料 — `GRASP_Z` / `PUSH_Z` / `EE_TO_FINGERTIP`（p11 ARM-CONTROL-DESIGN）**v2**

**依頼:** `MSG-PN-P11-FINGERTIP-BOUNDARY-MATERIALS-20260726-001`。**訂正:** `MSG-PN-P11-FINGERTIP-MATERIALS-RETURN-20260726-001`（B1〜B4・**全て私の原因**）。
**correction chain:** v1 `55d95a35f6b894dd54020fa0ec0eeb2ac8a89d1d`（sha256 `e561b53f49243a97…`）→ **本 v2**（v1 は git 履歴に保持・**rewrite なし**）。
⛔⛔ **owner を選ばない ／ 値を選ばない ／ 方式を選ばない ／ 推奨を書かない。** 分類は p5 側材料と合流後に **p17**。
**scope:** 設計/記録材料のみ。⛔ source / `[CHANGE]` / 実装 / RUN / verify / status / gate flip は CLOSED。**H-3.1 GO 無し・H-4 全体 HOLD** も不変。

---

## B1 応答 — ⭐ source closure（**citation tree を committed へ統一**）

⛔⛔ **v1 の欠陥（受理）**: 「on-disk 実測」と書きながら **as-read manifest を付けず**、**行番号は dirty working tree（WT）のもの**だった。⇒ **pN の指摘は私の再測で完全に一致**（下表）。

**⭐ 本 v2 は committed tree（blob）で統一して cite する。** 理由 = **blob は immutable で第三者が再現できる**（WT は他 pane の編集で動く）。

### 参照した全 source の manifest（`changed=[]` bracket つき）
- **読取前後の `git status --porcelain -- <全 path>` = 同一**（読取中に変化なし）⇒ `changed=[]`。

| path | taxonomy | **committed blob（cite 元）** | as_read WT sha256(16) | 行番号の差 |
|---|---|---|---|---|
| `thread_isaac_lab/configs/task_config.py` | **clean** | `d86380dbe186af00…` | `1a0851db9cfc2c74` | **同一** |
| `thread_isaac_lab/envs/newton_skill_env_base.py` | **clean** | `aaf15111377ac0c0…` | `e7a67ee34c50b78f` | **同一** |
| `thread_isaac_lab/envs/route_executor.py` | **clean** | `46f49d2722dbceda…` | `09db5a6d7e9d28e9` | **同一** |
| `thread_isaac_lab/skills/scripted_skills.py` | **clean** | `e8faa50c30f7d65b…` | `3586a1954720f829` | **同一** |
| `thread_isaac_lab/configs/mpc_config_grip.py` | **clean** | `6795ad3ad463940a…` | `62b20692d59d8e9f` | **同一** |
| ⚠`thread_isaac_lab/envs/newton_grip_env.py` | **modified** | `ae5985759fe30b8505f6a5914340932443ea70ac` | `8521e96335398b64` | **異なる**（v1 は WT `:118/:147/:435-436/:751/:757/:1163/:1169`／**committed `:113/:142/:430-431/:746/:752/:1158/:1164`**） |
| ⚠`thread_isaac_lab/envs/newton_approach_cable_mujoco_env.py` | **modified** | `515ebfbb63cc69797c9b25c532d31d5597669332` | `3544a78583caa9d8` | committed `:197-200`（v1 の `:196-199` は WT） |
| ⚠`thread_isaac_lab/scripts/newton_routing_utils.py` | **modified** | `b6eaf1a828feef00ae149179dc49d3fe90a8725d` | `23795ca75eec9e58` | **異なる**（WT `:1403/:1469/:1521-1522`, `:1730-1731/:1773-1774`／**committed `:1295/:1346/:1382-1383`, `:1568-1569/:1602-1603`**） |
| ⚠`thread_isaac_lab/skills/step_table.py` | **modified** | `1e18a63dcf14d9c6278d2c1fd094a447d1003696` | `ff1c0029e9e061b3` | committed `:32/:97`（本件の 2 行は同番号） |
| ⚠`thread_isaac_lab/scripts/test_newton_20clip_reachability.py` | **modified** | `c7b248719a38eb5dd9b0f98fe88b14aa11e71ace` | `d94137ef26518794` | **異なる**（v1 の `:58` は WT／**committed `:46`**） |

⚠ **`newton_grip_env.py` の committed blob を私が `git show | sha256sum` した値 = `1207554b257c97e3…`**（pN 提示値と一致）。⚠ **WT 値 `8521e96335398b64…`** も pN 提示の dirty-WT 値と一致。⇒ **pN の指摘は私の独立再測で確認済。**
⚠ **v1 の `newton_routing_utils.py` の path 記載も誤り**（`envs/` でなく **`scripts/`**）。

**⇒ 以下 §1〜§4 の行番号は、断りがない限り すべて上表の committed blob 上のもの。**

---

## B2 応答 — ⭐ consumer closure（**truncate せず全件を数えた**）

⛔⛔ **v1 の欠陥（受理）**: v1 の一覧は `head -12` 等で**切り詰めた出力**から書いており、そこから「**Grip skill のみが実質 consumer**」という **taxonomy 全体の結論**を出していた。⇒ ⛔ **当該結論を撤回する。**（**切り詰めた一覧は inventory ではない。**）

### 全件数（`grep -rn` を truncate せず集計・`thread-vault/` 除外）
| symbol | **総 hit 数** | file 数 |
|---|---|---|
| `GRASP_Z` | **99** | 21 |
| `PUSH_Z` | **53** | 11 |
| `EE_TO_FINGERTIP` | **74** | 19 |

### 階層別の分類（**tier は完全・行分類は §1〜§3 の operative tier のみ**）
| tier | path 群 | 扱い |
|---|---|---|
| **operative（env / skill）** | `envs/newton_grip_env.py`・`envs/newton_skill_env_base.py`・`envs/newton_approach_cable_mujoco_env.py`・`envs/route_executor.py`・`skills/scripted_skills.py`・`skills/step_table.py` | ⭐ **§1〜§3 で行単位に分類** |
| **config / SSOT** | `configs/task_config.py`（定義）・`configs/mpc_config_grip.py`・`configs/mpc_config_ic.py` | 同上（注記のみの hit を含む） |
| **harness / test / demo / builder** | `scripts/*`（`newton_routing_utils.py` / `test_*` / `build_*_precondition.py` / `generate_demos_*` / `demo_*` / `dry_run_*` / `plot_*` / `measure_*` / `collect_expert_demos.py` / `eval_skill.py` / `m4_phase0_*`）・`tests/*` | ⚠⚠ **file 単位でのみ分類し、行単位では分類していない**（**明示的に fence する**） |

⭐ **pN 指摘の脱漏を取り込み**: `scripts/newton_routing_utils.py`（committed）**`GRASP_Z` = `:53`(import) / `:1295` / `:1346` / `:1382-1383`**、**`PUSH_Z` = `:53` / `:1529`(docstring) / `:1568-1569` / `:1587`(comment) / `:1602-1603`**。**AerialRegrasp 系** = `scripts/build_aerial_regrasp_precondition.py`（`GRASP_Z` 8 / `EE_TO_FINGERTIP` 3）・`scripts/demo_aerial_regrasp.py`（`EE_TO_FINGERTIP` 3）・`scripts/generate_demos_mppi_m3_ar.py`（`GRASP_Z` 4 / `EE_TO_FINGERTIP` 6）。⇒ **いずれも harness/demo/builder tier**（⛔ 行単位の operative 判定はしていない）。

⇒ ⛔ **「実質 consumer は Grip skill のみ」とは言えない。** operative tier だけでも `newton_grip_env` / `scripted_skills` / `step_table` が consumer であり、harness tier には**多数**在る。**どこまでを operative と見なすかの判断は本書では行わない。**

---
## 0. ⭐ 先に、分類に効く 3 つの観測事実（値や owner の主張ではない）

| # | 観測事実（実測） | 出典（逐語） |
|---|---|---|
| **F-1** | **`GRASP_Z` / `PUSH_Z` は `route_c1_c2` code path では使われていない** | `route_executor.py:2450` 逐語「**GRASP_Z/PUSH_Z (task_config) are the LEGACY P1-P4 path, NOT used by route_c1_c2** -> the route descent target is **GROOVE_CENTER_Z+ee_off (dynamic)**」 |
| **F-2** | ⭐**`route_c1_c2` code path の降下目標は「観測量」で作られている** — `ee_off` は**実行時に測った値**（EE の実 z − 把持中 cable 分節の実 z） | `route_executor.py:2900` `ee_off = float(get_ee_positions(state, scene_info)[1][2]) - _seg_z_mm(GRASP_YC) / 1e3` ／ 使用 `:3106` `seat_ee_z` / `:4214` `c2_seat_ee_z = GROOVE_CENTER_Z + _clip_float_z + ee_off` |
| **F-3** | ⭐**ある env は既に `EE_TO_FINGERTIP` から離脱し、実測コ字値を使っている** | `newton_approach_cable_mujoco_env.py:197-199` 逐語「the koshape OPEN claw bottom reaches the cable centerline（**NOT 40mm into the table via the stale Franka GRASP_Z=1.025**）」＋ `EE_Z_FLOOR_KO = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS + **EE_TO_PINCH_OPEN**`（`:200`。`EE_TO_PINCH_OPEN = 0.26092`・`task_config.py:326`） |

⇒ **F-1〜F-3 は「3 定数が全 skill 共通の単一定数として実際に機能しているか」に直接効く**（本書 §4 の要求事実）。⛔ **どう分類するかは書かない。**

---

## 1. `EE_TO_FINGERTIP`（`task_config.py:78` = `0.220`）

### (1) 実 consumer・skill・source pin

| consumer | 位置 | 何に使っているか |
|---|---|---|
| **成功述語の測定点** | `newton_skill_env_base.py:899-905` `compute_clamp_pos` = `ee_pos + R(ee_q)·[0,0,+EE_TO_FINGERTIP]` | **live の acquire-grasp 判定**が使う点。判定連鎖 = `newton_grip_env.py:1158`/`:1164` `compute_clamp_pos` → `:1167` `cable_pos` → `:1169-1171` `find_nearest_cable_point(cable_pos, clamp_r_pos, …)` → `dist_pos` → `:1224-1232` `< CLAMP_DIST_THRESH`（= `T_DIST` 2 mm・`:223`） |
| **cable 分節の探索窓** | `newton_grip_env.py:746` / `:752`（`right_tip[2] -= EE_TO_FINGERTIP`） | 最近傍 cable 分節 index の決定（**z のみを引く軸固定の近似**・下記 (3) 参照） |
| **positioning 定数の材料** | `task_config.py:93` `GRASP_Z` / `:95` `PUSH_Z` | 両者の定義式に含まれる |
| **p11 側 spec** | 測定 spec §H-4.1 **J-a**（`ee_pos + 0.220·ẑ_ee`） | ⭐ **閾値が測っている点**として 3 参照点の 1 つに明示（他 = J-b pad 中点 / J-c `EE_TO_PINCH_TIP_CLOSED 0.2757`） |
| ⚠ 自己申告 | `task_config.py:78` 逐語「FRANKA panda_hand->fingertip」/ `:84`「220mm, **Franka value; re-derive S6**」/ `:324`「**EE_TO_FINGERTIP above (0.220) is the Franka/legacy**」 | **定数自身が legacy と宣言している** |

### (2) 腕側が必要とする measurement surface
- **腕の制御が要求するのは「閾値が評価される点」と同じ面**。⇒ gain sizing は **判定式が使う面**で行う必要がある（別の面で bar を立てると、満たしても判定は落ちる／その逆）。
- ⚠ **接触の物理が起きる面は別**: cable に実際に触れるのは **pad body**（`GRIPPER_PAD_BODY_IDX = [9,13]`・`task_config.py:37`）。**実測コ字値** = `EE_TO_PINCH_CLOSED 0.2548`（`:320`）/ `EE_TO_PINCH_TIP_CLOSED 0.2757`（`:321`）/ `EE_TO_PINCH_OPEN 0.26092`（`:326`）。⇒ **`0.220` と 34.8〜55.7 mm 違う**（= 2 mm 閾値の 17〜28 倍）。
- ⇒ **腕側の要求事実**: 「**どの面で bar を立てるか**」が決まらないと gain の下限が確定しない。⛔ **どちらにすべきかは本書で言わない**（H-4 は 3 面すべてを出す設計ゆえ、**面の選択のために新たな測定設計は要らない**。⚠ ただし **H-4 全体は HOLD** であり再測定の要否は別問題）。

### (3) frame / unit
- **unit = m**（`task_config.py` 全体の慣行）。
- **frame = EE body（wrist_3・local index 5・`task_config.py:30` `EE_BODY_IDX`）の local +Z**。⇒ `compute_clamp_pos` は **姿勢で回す**（`quat_rotate(ee_quat, [0,0,+EE_TO_FINGERTIP])`）。
- ⚠ **同じ定数が 2 通りに使われている**: `compute_clamp_pos` は **回転を掛ける**が、`newton_grip_env.py:746/752` は **world z から直に引く**（`tip[2] -= EE_TO_FINGERTIP`）。⇒ **後者は EE が傾くと誤差を持つ**（要求事実として記載・⛔ 是正は求めない）。

### (4) 要求事実（共通必要 / skill 別可分 / 観測量へ移せるか）
- **全 skill 共通である必要**: ⛔ **現状の実装は共通になっていない**（**F-3**: `newton_approach_cable_mujoco_env` は同じ役割に `EE_TO_PINCH_OPEN` を使い、`GRASP_Z=1.025` を「stale Franka」と明記）。⇒ **「共通でなければ成立しない」ことを示す実装事実は、私の court では観測されなかった。**
- **skill 別に分けられるか**: 現に **分かれている**（前項）。⚠ ただし **acquire-grasp の判定式**（`compute_clamp_pos`）と **cable 窓選択**（`:746/:752`）は**同一 env 内で同じ定数を共有**しており、この 2 つを分けた場合の影響は**私は測っていない**。
- **観測量へ移せるか**: ⭐ **`route_c1_c2` code path では移っている**（**F-2**: `ee_off` は実行時計測）。⚠ ただし **acquire-grasp の判定式は定数のまま**であり、判定面を観測量へ移す場合は **成功条件の変更**に当たる（＝ `/reward-design` の直交ゲート対象）。⛔ **可否は本書で判断しない。**

---

## 2. `GRASP_Z`（`task_config.py:93` = `TABLE_HEIGHT + CLIP_BASE_HEIGHT + EE_TO_FINGERTIP` = **1.025**）

### (1) 実 consumer・skill・source pin
| consumer | 位置 | 何に使っているか |
|---|---|---|
| **Grip skill の P0 前提** | `newton_grip_env.py:113` import / `:142` **`GRIP_Z = GRASP_Z + CABLE_RADIUS`**（逐語「1.029m: fingertip at cable center Z (0.809)」） | 把持開始高さ |
| MPC config（注記） | `mpc_config_grip.py:110` 逐語「Grip P0 precondition already positions arms at GRASP_Z (cable-proximal)」 | 前提の記述 |
| 到達性テスト | `test_newton_20clip_reachability.py:46` **独自に再定義**（`TABLE_HEIGHT + EE_TO_FINGERTIP`・**`CLIP_BASE_HEIGHT` を含まない**） | ⚠ **task_config の定義と一致しない別式**（要求事実として記載） |
| ⛔ **`route_c1_c2` code path** | — | **使っていない**（**F-1**） |

### (2) 腕側が必要とする measurement surface
- **これは「腕への指令 z」**（IK 目標）であり、**判定面ではない**。⇒ 腕側が要求するのは **指令が到達可能で、かつ静定後のたわみ込みで意図した面に載ること**。
- ⚠ **静的たわみが直に効く**: 実測 `τ_bias` 最大 **27.22 N·m** が `shoulder_lift`（`ke = 2000`）に載り **`Δq = 13.61 mrad`**（report `h3_torque_budget.per_joint_H3_1`）。⇒ **指令 z と実現 z はずれる**。⛔ **ずれの手先 [mm] は未確定**（合成 `‖Σ_i jacp[:,i]·Δq_i‖` が未測・H-4 の per-joint 列と対応付けが要る）。

### (3) frame / unit
- **unit = m**、**frame = world z**（`TABLE_HEIGHT` 起点の絶対高さ）。
- ⚠ **意味論は「fingertip が clip base top（= cable bottom）に来る wrist の z」**（`:93` 逐語）⇒ **`EE_TO_FINGERTIP` の意味に依存する派生量**。⇒ **`EE_TO_FINGERTIP` が変われば同じ式のまま値が動く。**

### (4) 要求事実
- **全 skill 共通である必要**: ⛔ **現に共通ではない**（`route_c1_c2` code path は不使用 = F-1／到達性テストは別式）。
- **skill 別に分けられるか**: **現に分かれている**（Grip skill のみが実質の consumer）。
- **観測量へ移せるか**: ⭐ **`route_c1_c2` code path 側は観測量**（F-2）。**Grip skill 側で同じ移行が可能かは私は測っていない**（P0 前提の作り方に依存）。⛔ 判断しない。

---

## 3. `PUSH_Z`（`task_config.py:95` = 同式 = **1.025**・逐語「same as GRASP_Z」）

### (1) 実 consumer・skill・source pin
| consumer | 位置 | 何に使っているか |
|---|---|---|
| **scripted skill の押込目標** | `skills/scripted_skills.py:39` import / `:88` `return (x, y, PUSH_Z)` | 押込みの EE 目標 |
| **工程表** | `skills/step_table.py:32` import / `:97` `return (cx, ly, PUSH_Z), (cx, ry, PUSH_Z)` | 左右の EE 目標 |
| Grip env | `newton_grip_env.py:123` import / `:430-431` `ee_left/ee_right = (CLIP1_X, CLIP1_Y ∓ GRIP_HALF_SPAN, PUSH_Z)` | 初期 EE 目標 |
| ⛔ **`route_c1_c2` code path** | — | **使っていない**（F-1） |

### (2) 腕側が必要とする measurement surface
- `GRASP_Z` と同じ（指令 z・判定面ではない）。⚠ **押込みは接触が効く局面**ゆえ、**§5.2 の「接触が効く瞬間の前に静定させる」要求が直接かかる**（静定判定は窓で行う）。
- ⚠ **`GRASP_Z` と数値が同一**（両者とも `1.025`）だが、**役割は別**（把持開始高さ vs 押込目標）。⇒ **値が同じことは、同じ量であることを意味しない。**

### (3) frame / unit
- `GRASP_Z` と同一（**m / world z**・`EE_TO_FINGERTIP` 依存の派生量）。

### (4) 要求事実
- **全 skill 共通である必要**: ⛔ **現に共通ではない**（`route_c1_c2` code path 不使用）。⚠ ただし **scripted skill と step_table が同じ値を共有**しており、**この 2 者の間では共通**。
- **skill 別に分けられるか**: **分けられている実装事実は無い**（上記 2 者は共有）。⚠ **分けた場合の影響は私は測っていない。**
- **観測量へ移せるか**: **`route_c1_c2` code path に前例あり**（F-2）。⛔ **scripted 経路で可能かは未測・判断しない。**

---

## 4. ⭐ 3 定数を横に見たときの要求事実（分類の入力・⛔ 分類ではない）

| 軸 | 実測事実 |
|---|---|
| **共有の実態** | **`EE_TO_FINGERTIP` だけが 3 者の根** — `GRASP_Z` / `PUSH_Z` は**その派生量**（同じ式・同じ値 1.025）。⇒ **根を動かせば 2 つが同時に動く。** |
| **共通性** | ⛔ **3 定数とも「全 skill 共通」として機能していない**（`route_c1_c2` code path 不使用 = F-1／approach env は別値へ離脱 = F-3／到達性テストは別式） |
| **観測量への移行** | ⭐ **`route_c1_c2` code path では実装済**（`ee_off` = 実行時計測・F-2）。⚠ **成功述語側は定数のまま** ⇒ そこを移すのは **成功条件の変更**（`/reward-design` 直交ゲート対象） |
| **面の不一致** | **判定面（`0.220`）と接触面（pad・実測 `0.2548`/`0.2757`/`0.26092`）が 34.8〜55.7 mm 違う** ＝ **2 mm 閾値の 17〜28 倍** |
| **腕側の依存** | ⭐ **面の選択それ自体は、新たな measurement-design point を増やさない** — H-4 は **3 参照点**を出す設計（`53b8997ed4`）ゆえ、どの面に決まっても**そのための追加設計は不要**。⛔⛔ **「再測定不要」とは言えない** — **H-4 全体は HOLD 継続**であり、**認可済みの rerun および H-4 の他の欠陥・要求（例: literal `(9,13)` の carry・envelope が 1 姿勢）は残る**（RETURN B4 受理） |
| ⚠ **同一定数の 2 用法** | `compute_clamp_pos` は**姿勢で回す**／`newton_grip_env.py:746/752` は **world z から直に引く** ⇒ **EE が傾くと後者に誤差**（⛔ 是正は求めない・事実の記載のみ） |

---

## 5. B3 / B4 応答（要点の再掲）

- **B3**: 「**現行 route** / **production route**」という **status 主張を撤回**。source が示すのは **`route_executor.py` の `route_c1_c2` code path の挙動**のみ ⇒ 全箇所を「**`route_c1_c2` code path**」へ置換した。⛔ **どの route が現行かを述べる authority/status SSOT を私は exact-pin していない。**
- **B4**: 「**どれに決まっても再測定不要**」という**絶対主張を撤回**。正しくは **「面の選択それ自体は新たな measurement-design point を増やさない」**まで。⛔ **H-4 全体は HOLD 継続**であり、**認可済み rerun および H-4 の他の欠陥・要求（literal `(9,13)` の carry／envelope が 1 姿勢 等）は残る**。

## 5.1 非主張

- ⛔ **owner を書いていない**（`GRASP_Z`/`PUSH_Z`/`EE_TO_FINGERTIP` の court は **UNCONFIRMED / HOLD**・候補 p5 / p17 / p11 / p16）。**私は自分を owner とも他者とも書かない。**
- ⛔ **値・方式・推奨を書いていない。** 分類は p17（p5 側材料と合流後）。
- **p5 の材料を私は再解釈していない**（本書は**腕側 consumer の実測**のみ）。
- **未測と明記した項目**: 手先たわみの合成量 `‖Σ_i jacp[:,i]·Δq_i‖`／定数を skill 別に分けた場合の影響／Grip・scripted 経路で観測量へ移せるか。
