# 腕側 consumer レビュー材料 — `GRASP_Z` / `PUSH_Z` / `EE_TO_FINGERTIP`（p11 ARM-CONTROL-DESIGN）

**依頼:** `MSG-PN-P11-FINGERTIP-BOUNDARY-MATERIALS-20260726-001`（pN 経由）。**本書は材料のみ。**
⛔⛔ **owner を選ばない ／ 値を選ばない ／ 方式を選ばない。** 分類（taxonomy）は p5 側材料と合流後に **p17** が行う。**本書に推奨は書かない。**
**scope:** 設計/記録材料のみ。⛔ source / `[CHANGE]` / 実装 / RUN / verify / status / gate flip は CLOSED。**H-3.1 GO 無し・H-4 全体 HOLD** も不変。
**根拠:** 下記はすべて **p11 が on-disk で実測**した（他 pane の relay を根拠にしていない）。

---

## 0. ⭐ 先に、分類に効く 3 つの観測事実（値や owner の主張ではない）

| # | 観測事実（実測） | 出典（逐語） |
|---|---|---|
| **F-1** | **`GRASP_Z` / `PUSH_Z` は現行 route の経路では使われていない** | `route_executor.py:2450` 逐語「**GRASP_Z/PUSH_Z (task_config) are the LEGACY P1-P4 path, NOT used by route_c1_c2** -> the route descent target is **GROOVE_CENTER_Z+ee_off (dynamic)**」 |
| **F-2** | ⭐**route の降下目標は既に「観測量」で作られている** — `ee_off` は**実行時に測った値**（EE の実 z − 把持中 cable 分節の実 z） | `route_executor.py:2900` `ee_off = float(get_ee_positions(state, scene_info)[1][2]) - _seg_z_mm(GRASP_YC) / 1e3` ／ 使用 `:3106` `seat_ee_z` / `:4214` `c2_seat_ee_z = GROOVE_CENTER_Z + _clip_float_z + ee_off` |
| **F-3** | ⭐**ある env は既に `EE_TO_FINGERTIP` から離脱し、実測コ字値を使っている** | `newton_approach_cable_mujoco_env.py:196-199` 逐語「the koshape OPEN claw bottom reaches the cable centerline（**NOT 40mm into the table via the stale Franka GRASP_Z=1.025**）」＋ `EE_Z_FLOOR_KO = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS + **EE_TO_PINCH_OPEN**`（`:200`。`EE_TO_PINCH_OPEN = 0.26092`・`task_config.py:326`） |

⇒ **F-1〜F-3 は「3 定数が全 skill 共通の単一定数として実際に機能しているか」に直接効く**（本書 §4 の要求事実）。⛔ **どう分類するかは書かない。**

---

## 1. `EE_TO_FINGERTIP`（`task_config.py:78` = `0.220`）

### (1) 実 consumer・skill・source pin

| consumer | 位置 | 何に使っているか |
|---|---|---|
| **成功述語の測定点** | `newton_skill_env_base.py:899-905` `compute_clamp_pos` = `ee_pos + R(ee_q)·[0,0,+EE_TO_FINGERTIP]` | **live の acquire-grasp 判定**が使う点。判定連鎖 = `newton_grip_env.py:1163`/`:1169` → `:1172` `cable_pos` → `:1174-1176` `find_nearest_cable_point(cable_pos, clamp_r_pos, …)` → `dist_pos` → `:1229-1236` `< CLAMP_DIST_THRESH`（= `T_DIST` 2 mm・`:228`） |
| **cable 分節の探索窓** | `newton_grip_env.py:751` / `:757`（`right_tip[2] -= EE_TO_FINGERTIP`） | 最近傍 cable 分節 index の決定（**z のみを引く軸固定の近似**・下記 (3) 参照） |
| **positioning 定数の材料** | `task_config.py:93` `GRASP_Z` / `:95` `PUSH_Z` | 両者の定義式に含まれる |
| **p11 側 spec** | 測定 spec §H-4.1 **J-a**（`ee_pos + 0.220·ẑ_ee`） | ⭐ **閾値が測っている点**として 3 参照点の 1 つに明示（他 = J-b pad 中点 / J-c `EE_TO_PINCH_TIP_CLOSED 0.2757`） |
| ⚠ 自己申告 | `task_config.py:78` 逐語「FRANKA panda_hand->fingertip」/ `:84`「220mm, **Franka value; re-derive S6**」/ `:324`「**EE_TO_FINGERTIP above (0.220) is the Franka/legacy**」 | **定数自身が legacy と宣言している** |

### (2) 腕側が必要とする measurement surface
- **腕の制御が要求するのは「閾値が評価される点」と同じ面**。⇒ gain sizing は **判定式が使う面**で行う必要がある（別の面で bar を立てると、満たしても判定は落ちる／その逆）。
- ⚠ **接触の物理が起きる面は別**: cable に実際に触れるのは **pad body**（`GRIPPER_PAD_BODY_IDX = [9,13]`・`task_config.py:37`）。**実測コ字値** = `EE_TO_PINCH_CLOSED 0.2548`（`:320`）/ `EE_TO_PINCH_TIP_CLOSED 0.2757`（`:321`）/ `EE_TO_PINCH_OPEN 0.26092`（`:326`）。⇒ **`0.220` と 34.8〜55.7 mm 違う**（= 2 mm 閾値の 17〜28 倍）。
- ⇒ **腕側の要求事実**: 「**どの面で bar を立てるか**」が決まらないと gain の下限が確定しない。⛔ **どちらにすべきかは本書で言わない**（H-4 は 3 面すべてを出す設計ゆえ **私の作業は止まらない**）。

### (3) frame / unit
- **unit = m**（`task_config.py` 全体の慣行）。
- **frame = EE body（wrist_3・local index 5・`task_config.py:30` `EE_BODY_IDX`）の local +Z**。⇒ `compute_clamp_pos` は **姿勢で回す**（`quat_rotate(ee_quat, [0,0,+EE_TO_FINGERTIP])`）。
- ⚠ **同じ定数が 2 通りに使われている**: `compute_clamp_pos` は **回転を掛ける**が、`newton_grip_env.py:751/757` は **world z から直に引く**（`tip[2] -= EE_TO_FINGERTIP`）。⇒ **後者は EE が傾くと誤差を持つ**（要求事実として記載・⛔ 是正は求めない）。

### (4) 要求事実（共通必要 / skill 別可分 / 観測量へ移せるか）
- **全 skill 共通である必要**: ⛔ **現状の実装は共通になっていない**（**F-3**: `newton_approach_cable_mujoco_env` は同じ役割に `EE_TO_PINCH_OPEN` を使い、`GRASP_Z=1.025` を「stale Franka」と明記）。⇒ **「共通でなければ成立しない」ことを示す実装事実は、私の court では観測されなかった。**
- **skill 別に分けられるか**: 現に **分かれている**（前項）。⚠ ただし **acquire-grasp の判定式**（`compute_clamp_pos`）と **cable 窓選択**（`:751/:757`）は**同一 env 内で同じ定数を共有**しており、この 2 つを分けた場合の影響は**私は測っていない**。
- **観測量へ移せるか**: ⭐ **route 経路では既に移っている**（**F-2**: `ee_off` は実行時計測）。⚠ ただし **acquire-grasp の判定式は定数のまま**であり、判定面を観測量へ移す場合は **成功条件の変更**に当たる（＝ `/reward-design` の直交ゲート対象）。⛔ **可否は本書で判断しない。**

---

## 2. `GRASP_Z`（`task_config.py:93` = `TABLE_HEIGHT + CLIP_BASE_HEIGHT + EE_TO_FINGERTIP` = **1.025**）

### (1) 実 consumer・skill・source pin
| consumer | 位置 | 何に使っているか |
|---|---|---|
| **Grip skill の P0 前提** | `newton_grip_env.py:118` import / `:147` **`GRIP_Z = GRASP_Z + CABLE_RADIUS`**（逐語「1.029m: fingertip at cable center Z (0.809)」） | 把持開始高さ |
| MPC config（注記） | `mpc_config_grip.py:110` 逐語「Grip P0 precondition already positions arms at GRASP_Z (cable-proximal)」 | 前提の記述 |
| 到達性テスト | `test_newton_20clip_reachability.py:58` **独自に再定義**（`TABLE_HEIGHT + EE_TO_FINGERTIP`・**`CLIP_BASE_HEIGHT` を含まない**） | ⚠ **task_config の定義と一致しない別式**（要求事実として記載） |
| ⛔ **route 経路** | — | **使っていない**（**F-1**） |

### (2) 腕側が必要とする measurement surface
- **これは「腕への指令 z」**（IK 目標）であり、**判定面ではない**。⇒ 腕側が要求するのは **指令が到達可能で、かつ静定後のたわみ込みで意図した面に載ること**。
- ⚠ **静的たわみが直に効く**: 実測 `τ_bias` 最大 **27.22 N·m** が `shoulder_lift`（`ke = 2000`）に載り **`Δq = 13.61 mrad`**（report `h3_torque_budget.per_joint_H3_1`）。⇒ **指令 z と実現 z はずれる**。⛔ **ずれの手先 [mm] は未確定**（合成 `‖Σ_i jacp[:,i]·Δq_i‖` が未測・H-4 の per-joint 列と対応付けが要る）。

### (3) frame / unit
- **unit = m**、**frame = world z**（`TABLE_HEIGHT` 起点の絶対高さ）。
- ⚠ **意味論は「fingertip が clip base top（= cable bottom）に来る wrist の z」**（`:93` 逐語）⇒ **`EE_TO_FINGERTIP` の意味に依存する派生量**。⇒ **`EE_TO_FINGERTIP` が変われば同じ式のまま値が動く。**

### (4) 要求事実
- **全 skill 共通である必要**: ⛔ **現に共通ではない**（route は不使用 = F-1／到達性テストは別式）。
- **skill 別に分けられるか**: **現に分かれている**（Grip skill のみが実質の consumer）。
- **観測量へ移せるか**: ⭐ **route 側は既に観測量**（F-2）。**Grip skill 側で同じ移行が可能かは私は測っていない**（P0 前提の作り方に依存）。⛔ 判断しない。

---

## 3. `PUSH_Z`（`task_config.py:95` = 同式 = **1.025**・逐語「same as GRASP_Z」）

### (1) 実 consumer・skill・source pin
| consumer | 位置 | 何に使っているか |
|---|---|---|
| **scripted skill の押込目標** | `skills/scripted_skills.py:39` import / `:88` `return (x, y, PUSH_Z)` | 押込みの EE 目標 |
| **工程表** | `skills/step_table.py:32` import / `:97` `return (cx, ly, PUSH_Z), (cx, ry, PUSH_Z)` | 左右の EE 目標 |
| Grip env | `newton_grip_env.py:128` import / `:435-436` `ee_left/ee_right = (CLIP1_X, CLIP1_Y ∓ GRIP_HALF_SPAN, PUSH_Z)` | 初期 EE 目標 |
| ⛔ **route 経路** | — | **使っていない**（F-1） |

### (2) 腕側が必要とする measurement surface
- `GRASP_Z` と同じ（指令 z・判定面ではない）。⚠ **押込みは接触が効く局面**ゆえ、**§5.2 の「接触が効く瞬間の前に静定させる」要求が直接かかる**（静定判定は窓で行う）。
- ⚠ **`GRASP_Z` と数値が同一**（両者とも `1.025`）だが、**役割は別**（把持開始高さ vs 押込目標）。⇒ **値が同じことは、同じ量であることを意味しない。**

### (3) frame / unit
- `GRASP_Z` と同一（**m / world z**・`EE_TO_FINGERTIP` 依存の派生量）。

### (4) 要求事実
- **全 skill 共通である必要**: ⛔ **現に共通ではない**（route 不使用）。⚠ ただし **scripted skill と step_table が同じ値を共有**しており、**この 2 者の間では共通**。
- **skill 別に分けられるか**: **分けられている実装事実は無い**（上記 2 者は共有）。⚠ **分けた場合の影響は私は測っていない。**
- **観測量へ移せるか**: **route 側の前例あり**（F-2）。⛔ **scripted 経路で可能かは未測・判断しない。**

---

## 4. ⭐ 3 定数を横に見たときの要求事実（分類の入力・⛔ 分類ではない）

| 軸 | 実測事実 |
|---|---|
| **共有の実態** | **`EE_TO_FINGERTIP` だけが 3 者の根** — `GRASP_Z` / `PUSH_Z` は**その派生量**（同じ式・同じ値 1.025）。⇒ **根を動かせば 2 つが同時に動く。** |
| **共通性** | ⛔ **3 定数とも「全 skill 共通」として機能していない**（route 不使用 = F-1／approach env は別値へ離脱 = F-3／到達性テストは別式） |
| **観測量への移行** | ⭐ **production route では既に完了**（`ee_off` = 実行時計測・F-2）。⚠ **成功述語側は定数のまま** ⇒ そこを移すのは **成功条件の変更**（`/reward-design` 直交ゲート対象） |
| **面の不一致** | **判定面（`0.220`）と接触面（pad・実測 `0.2548`/`0.2757`/`0.26092`）が 34.8〜55.7 mm 違う** ＝ **2 mm 閾値の 17〜28 倍** |
| **腕側の依存** | ⭐ **私の作業は 3 定数の決着を待たない** — H-4 を **3 参照点**で出す設計にしてある（`53b8997ed4`）⇒ **どれに決まっても再測定不要** |
| ⚠ **同一定数の 2 用法** | `compute_clamp_pos` は**姿勢で回す**／`newton_grip_env.py:751/757` は **world z から直に引く** ⇒ **EE が傾くと後者に誤差**（⛔ 是正は求めない・事実の記載のみ） |

---

## 5. 非主張

- ⛔ **owner を書いていない**（`GRASP_Z`/`PUSH_Z`/`EE_TO_FINGERTIP` の court は **UNCONFIRMED / HOLD**・候補 p5 / p17 / p11 / p16）。**私は自分を owner とも他者とも書かない。**
- ⛔ **値・方式・推奨を書いていない。** 分類は p17（p5 側材料と合流後）。
- **p5 の材料を私は再解釈していない**（本書は**腕側 consumer の実測**のみ）。
- **未測と明記した項目**: 手先たわみの合成量 `‖Σ_i jacp[:,i]·Δq_i‖`／定数を skill 別に分けた場合の影響／Grip・scripted 経路で観測量へ移せるか。
