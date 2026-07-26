# 訂正版 — 境界材料の source-closure / 計数 / taxonomy 訂正（原因側 = p5）

**stable ID:** `P5-BOUNDARY-MATERIALS-CORRECTION-20260726-001`
**著者:** SKILL-DETAIL-DESIGN (`w2:p5`) = **原因側**。**発行:** 2026-07-26T17:48:03+09:00（shell 実測）。
**契機:** pN RETURN `MSG-PN-P5-FINGERTIP-MATERIALS-RETURN-20260726-001`（B1-B5・taxonomy material HOLD・p17 relay CLOSED pending correction）。
**訂正対象（旧・immutable・書き換えない）:** `P5_BOUNDARY_MATERIALS_GRASPZ_PUSHZ_EETOFINGERTIP_20260726.md` @ commit `46377eef9f79efc20acc7e8bfdee739c5f35a09c` / sha256 `3248991e4817e67e2d7b73787eacd28cc065fc074f1251da034692b4938e232f`。
⭐ **B1-B5 の 5 件すべて、p5 が独立実測で CONFIRM**（pN の提示値と一致し、かつ **B1/B2 は pN の指摘より範囲が広い**）。
⛔ **owner / 値 / 方式は引き続き非選択。** source / `[CHANGE]` / 実装 / RUN / verify / status / gate flip = **CLOSED**。他 pane の record は編集しない。

---

## 0. 根本原因（1 個 + 2 個）

- **B1 と B2 は同一根**: **私は working tree を読み、どの tree を指すかを宣言せずに、banked artifact に行番号と件数を書いた。** ⇒ 既記録規律 [[feedback-pin-over-committed-state-not-dirty-tree-verify-in-worktree-2026-07-19]] / [[feedback-verify-on-disk-at-the-producing-commit-not-at-head-2026-07-14]] の違反。**pN の数値も私の数値も各々の tree では真**だが、banked artifact の主張としては **banked tree が参照面**であり、宣言なしの混在は再現不能。
- **B3** = 自 artifact 内の矛盾（要約行が本文の結論と逆）。
- **B4 / B5** = **同一性・接触を未検証のまま事実として書いた**（識別性の欠落）。[[feedback-a-predicate-that-cannot-discriminate-is-not-evidence-2026-07-21]] 同族。

---

## 1. B1 訂正 — source closure（path × taxonomy × full sha256 × 行番号が指す tree）

⭐ **行番号が指す tree = as-read working tree（読取 2026-07-26T17:2x–17:35 JST）**。banked tree ではない。

| path | tracked | 状態 | banked blob sha256 | as_read (WT) sha256 |
|---|---|---|---|---|
| `thread_isaac_lab/configs/task_config.py` | tracked | **clean** | `1a0851db9cfc2c740c98821c73c84f5405d1cc96df5fe22a71f66906bb1762bc` | 同一 |
| `thread_isaac_lab/envs/newton_skill_env_base.py` | tracked | **clean** | `e7a67ee34c50b78ff02baba4ab1bfe7b6002b1b2dfee15948e2c6795ad954fb9` | 同一 |
| `thread_isaac_lab/envs/route_executor.py` | tracked | **clean** | `09db5a6d7e9d28e9eebdcf568636b8f059545c077f919fa8e1f9e7014082c599` | 同一 |
| `thread_isaac_lab/skills/scripted_skills.py` | tracked | **clean** | `3586a1954720f82950a6f1e0698a621cdb1c7e2c2556efdf0bfc5f93f8889fca` | 同一 |
| `thread_isaac_lab/configs/mpc_config_ic.py` | tracked | **clean** | `37d185fcaced27caf1539a08d6d96504799934f02a4a61c6bfd0b0c3b2d69699` | 同一 |
| `thread_isaac_lab/configs/mpc_config_grip.py` | tracked | **clean** | `62b20692d59d8e9fb3325c12f28b301499ac2e1ac2acdce5b69d370b79268cbf` | 同一 |
| `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/2f85_koshape.xml` | tracked | **clean** | `a3bef79ee9b4f4161dd6da20967e65e0da78f5706724fbf61e35fb43ba230ba3` | 同一 |
| `thread_isaac_lab/envs/newton_grip_env.py` | tracked | ⚠**MODIFIED** | `1207554b257c97e3115fca303860bb25e072b5c69cb9bc0fef783d8c8267d147` | `8521e96335398b648f6dddf6eec7de1c6130276c42c55d9476c297d6d4f34df4` |
| `thread_isaac_lab/envs/newton_approach_cable_mujoco_env.py` | tracked | ⚠**MODIFIED** | `73ac245268084472574555fc7e03f3ec6cfeff78f78bfaef96d0ea25699221cd` | `3544a78583caa9d86d45616528a2b5efcdc524ba970c1a855c443ef826692bb8` |
| `thread_isaac_lab/skills/step_table.py` | tracked | ⚠**MODIFIED** | `6f9c3fb3d0010721c9287b8b63e2e86e7cecd7210e8ee8c2f222becaf3e5422b` | `ff1c0029e9e061b33a8bd7ff004703f89c136835ea5b4b7a1e81cb369017c649` |
| `thread_isaac_lab/scripts/test_newton_clip_routing.py` | tracked | ⚠**MODIFIED** | `2e1fc1d84539877f91cc75eb1f6443a628dfb0743bd24cb7f0e8a1ab956779dd` | `312e80d522a6e6d6667b070a024244cf9680227d23f50f6c528613644cffb345` |
| `thread_isaac_lab/scripts/newton_routing_utils.py` | tracked | ⚠**MODIFIED** | `bac4fbc92984b2e506ce095b7ee5d6ce4641da87536ad351269dae4995ecc137` | `23795ca75eec9e58d058aad11b08326879b07bef046e375d2086c06ae984ac85` |
| `harness/scripts/predict_training.py` | ⛔**untracked** | **commit tree に不在** | （不在 — `git cat-file` 空。空入力の sha256 = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`） | `7117860535ad2c95a9377eb85c7aa853d93a2e5d085a57b59ffdecffa7ee3401` |

**`changed = [newton_grip_env.py, newton_approach_cable_mujoco_env.py, step_table.py, test_newton_clip_routing.py, newton_routing_utils.py]`／`untracked = [harness/scripts/predict_training.py]`／`clean = 残り 7 path`。**

### 1-a. 行番号 delta（banked tree での正しい位置）

**`newton_grip_env.py` = 一律 −5 行**（他 4 file は引用箇所の行番号が banked と一致・内容照合済）:

| 引用内容 | 旧 artifact（WT） | **banked での正** |
|---|---|---|
| `GRIP_Z = GRASP_Z + CABLE_RADIUS` | `:147` | **`:142`** |
| `ee_left/ee_right = (…, PUSH_Z)` | `:435`/`:436` | **`:430`/`:431`** |
| `self._finger_physics_ids = []` | `:649` | **`:644`** |
| `tip[2] -= EE_TO_FINGERTIP` | `:751`/`:757` | **`:746`/`:752`**（pN 提示値と一致） |
| `compute_clamp_pos(ee_*_pos, …)` | `:1163`/`:1169` | **`:1158`/`:1164`** |
| `dist_pos_r < self.CLAMP_DIST_THRESH` | `:1230` | **`:1225`** |

⭐ **banked tree で新たに判明した consumer（旧 artifact の列挙漏れ）**: `compute_clamp_pos` の呼び出しが **`:1610` / `:1617`** にも存在する。⇒ 旧 artifact の consumer 列挙は **不完全**（success 判定以外の呼出面がある）。用途の同定は本書では行わない（材料の追加のみ）。

### 1-b. `predict_training.py`
旧 artifact は `harness/scripts/predict_training.py`×2 を consumer 表に載せたが、**当該 commit tree に存在しない**（untracked）。⇒ **consumer 表から除外**し、untracked 別掲に移す。

---

## 2. B2 訂正 — 再現可能な exact query / scope / output ＋ 役割分類

### 2-a. exact query（banked・再現可能）
```
git grep -c -E '\b<CONST>\b' 46377eef9f79efc20acc7e8bfdee739c5f35a09c \
  -- 'thread_isaac_lab/**/*.py' 'harness/**/*.py'
```
**旧 artifact の数値の出所**（再現不能だった query）:
```
grep -rn --include='*.py' --exclude-dir=.git --exclude-dir=.codex --exclude-dir=.claude \
  --exclude-dir=node_modules "\b<CONST>\b" .  | grep -v pre_3c_backup
```
⇒ **working tree 対象**であり banked と一致しない。

### 2-b. banked vs WT の **全 delta（10 件・pN 指摘 3 件を含む）**

| 定数 | path | banked | WT（旧 artifact の値） |
|---|---|---|---|
| `EE_TO_FINGERTIP` | `harness/scripts/predict_training.py` | **0（不在）** | 2 |
| `EE_TO_FINGERTIP` | `thread_isaac_lab/tests/test_env_refactor_bit_identical.py` | **0** | 2（未記載） |
| `EE_TO_FINGERTIP` | `thread_isaac_lab/tests/test_env_refactor_helpers.py` | **0** | 4（未記載） |
| `GRASP_Z` | `thread_isaac_lab/scripts/test_diagonal_reach.py` | **13** | 7 |
| `GRASP_Z` | `thread_isaac_lab/scripts/test_motion_sequence_dry_run.py` | **11** | 13 |
| `GRASP_Z` | `thread_isaac_lab/scripts/collect_expert_demos.py` | **3** | 2 |
| `GRASP_Z` | `thread_isaac_lab/scripts/demo_aerial_regrasp.py` | **1** | 0（**記載漏れ**） |
| `GRASP_Z` | `harness/orchestrator/harness_integration_test.py` | **0** | 4 |
| `PUSH_Z` | `thread_isaac_lab/scripts/collect_expert_demos.py` | **1** | 0（記載漏れ） |
| `PUSH_Z` | `thread_isaac_lab/scripts/dry_run_39step.py` | **1** | 0（記載漏れ） |

**banked 総計（本書の参照面）**: `EE_TO_FINGERTIP` = 17 file / 68 hit ／ `GRASP_Z` = 22 file / 105 hit ／ `PUSH_Z` = 13 file / 55 hit。

### 2-c. 役割分類（banked・**operative-candidate のみ列挙**。probe-script は集計のみ）

| 定数 | operative-candidate（file:hit） | probe-script |
|---|---|---|
| `EE_TO_FINGERTIP` | `configs/task_config.py`:5 / `envs/newton_grip_env.py`:3 / `envs/newton_skill_env_base.py`:3 / `configs/mpc_config_ic.py`:1 | 13 file / 56 hit |
| `GRASP_Z` | `configs/task_config.py`:3 / `envs/newton_grip_env.py`:3 / `configs/mpc_config_grip.py`:1 / `envs/newton_approach_cable_mujoco_env.py`:1 / `envs/route_executor.py`:1 | 17 file / 96 hit |
| `PUSH_Z` | `envs/newton_grip_env.py`:3 / `skills/scripted_skills.py`:2 / `skills/step_table.py`:2 / `configs/task_config.py`:1 / `envs/route_executor.py`:1 | 8 file / 46 hit |

⚠⚠ **分類は path 由来の役割であって稼働証明ではない（liveness は UNVERIFIED）。** pN の「tracked `*.py` だけから live を推論しない」に従い、以下を明記する:
- ⭐ **反例あり**: `scripts/newton_routing_utils.py` は path 上 probe-script だが、**`envs/route_executor.py`（`:1910`/`:2144`/`:3040`/`:3041`/`:3893`）と `skills/scripted_skills.py`（`:124`/`:244`/`:288`/`:336` 他）から import される library**（banked 実測）。⇒ **path bucket ≠ reachability**（本 arc で私が別件で立てた指摘と同型）。
- `envs/route_executor.py` の `GRASP_Z`/`PUSH_Z` hit は **legacy 宣言そのもの**（`:2450`「LEGACY P1-P4 path, NOT used by `route_c1_c2`」）⇒ operative path にあるが **operative な消費ではない**。
- ⇒ **operative/legacy/harness/test/probe/snapshot の確定分類には runtime 証拠（実行経路）が要る。本書は静的分類に留める。**

### 2-d. 自己検出した query 欠陥（記録）
本訂正の作業中、`git grep … -- 'thread_isaac_lab/skills/**/*.py'` が **`skills/` 直下の file に一致せず 0 hit** を返した。0 を不在の根拠にせず検索対象集合（`skills/` の `*.py` = 5 file）を確認して pathspec を `'thread_isaac_lab/skills/'` に修正した結果、上記の library import が判明した。⇒ **pathspec の `**` は直下を覆わない**ことを本書に記録する。

---

## 3. B3 訂正 — 自 artifact 内の矛盾

**RETRACT（旧 artifact `:32`）**: 「| `task_config.py:93` / `:95` | `GRASP_Z` / `PUSH_Z` を導出 | **全 skill 横断（下流全部）** |」の **「全 skill 横断（下流全部）」**。
⇒ 旧 artifact 自身の `:54` / `:81` / `:115` が「approach(mujoco) と route は非消費」と正しく述べており、`:32` はそれと矛盾していた。

**正**: `task_config.py:93`/`:95` の**派生先は `GRASP_Z` / `PUSH_Z` の 2 定数**。その consumer は §2-c の operative-candidate 集合（`newton_grip_env` / `scripted_skills` / `step_table` / `mpc_config_grip` / `task_config` 内部）＋ probe-script 群。⛔ **`approach`(mujoco) と `route_c1_c2` は非消費**（`newton_approach_cable_mujoco_env.py:197`／`route_executor.py:2450`）。
⇒ ⭐ **「全 skill 共通は現状の事実でない」という結論は保持**（B3 は要約行の誤りであり結論の誤りではない）。

---

## 4. B4 訂正 — 「観測移行の live 先例」を格下げ

**RETRACT（旧 artifact §1(4) / §4③）**: 「Z-Check が **finger body z** を定数なしで直読 ⇒ **観測移行の live 先例**」および「index 規約が **2 つ対等に併存**」。

**保持する事実（banked）**: `test_newton_clip_routing.py:466` = `body_q[bs + EE_BODY_OFFSET][2]`（hand z）／`:468-469` = `body_q[bs+7][2]`, `body_q[bs+8][2]` ⇒ **生の BODY-space index による per-body z 読み取りが live code に存在する**。

⛔ **UNVERIFIED へ移す**: その `+7` / `+8` が **pad / finger body かは未検証**。SSOT は pad-carrying followers を **`[9, 13]`** と定義（`task_config.py:37` `GRIPPER_PAD_BODY_IDX = [9, 13]  # BODY space: pad-carrying followers`／`:48` `FINGER_LOCAL = GRIPPER_PAD_BODY_IDX  # [9,13] (BODY-space finger-pos reads)`）。同 `:47` `EE_BODY_OFFSET = 5` と同じ BODY 空間の index 系である。
⇒ **`+7`/`+8` と `[9,13]` は stale / mismatch の候補**であり、「対等な 2 規約」ではない（pN 指摘どおり）。**同一性が解決するまで pad/finger としての妥当性は UNVERIFIED。**

⇒ **「観測量へ移せる」の残る根拠は asset に pad body が実在すること**（`2f85_koshape.xml:107` `right_pad` / `:154` `left_pad`）**に限定**する。⛔ **既存の read が pad を観測している証拠は無い。**

---

## 5. B5 訂正 — 「物理接触面 = f1ext 爪先」を UNMEASURED へ

**RETRACT（旧 artifact §1(2)）**: 「物理接触が起きる面は **コ f1ext 爪先**」。

**保持する asset 幾何事実**: pad body（`:107`/`:154`）／その上の geom `right_pad_f1ext`・`right_pad_f2ext`（`:116`/`:117`・local `pos` 明記）／`EE_TO_PINCH_TIP_CLOSED` は「pad TIP drop（コ f1ext claw tip）」を測った値という**記述**（`task_config.py:321`）。

⛔ **実際の接触 geom は UNMEASURED。** 反証材料（banked `route_executor.py:2436-2440`）:
- `:2436-2437` 逐語「retention = the cable is **SANDWICHED between the two claws (f1ext bottom + f2ext top**, mouth ~10mm, Ø8 cable -> ~2mm play; `GD-KoShape-Finger.md:51-58`)」
- `:2438` 逐語「The OLD **f1ext-only** gate false-FAILed "cable risen to the TOP claw under drag"」
⇒ **単一 geom を接触面と断定できない**（live gate は両爪＋横方向 footprint で判定）。接触面の同定には測定が要る。

---

## 6. 影響を受けない結論（保持・帳尻合わせで変えない）

1. **3 定数は独立でない** — `GRASP_Z`/`PUSH_Z` は `EE_TO_FINGERTIP` の派生（`task_config.py:93`/`:95`・clean file）。
2. ⭐ **「全 skill 共通」は現状の事実でない** — 3 面併存: acquire-grasp = 0.220 系（`newton_grip_env.py` banked `:142` `GRIP_Z`）／approach(mujoco) = コ `EE_TO_PINCH_OPEN`（`newton_approach_cable_mujoco_env.py:197` 逐語「stale Franka `GRASP_Z=1.025`」・`:200` `EE_Z_FLOOR_KO`・**両行は banked でも同一行番号**）／route = 動的 `GROOVE_CENTER_Z + ee_off`（`route_executor.py:2450`・clean file）。
3. ⚠ **frame 2 種混在** — EE-local を quat 回転して加算（`newton_skill_env_base.py:902`・clean）vs world −Z 直接減算（`newton_grip_env.py` banked **`:746`/`:752`**）。**一致は特定姿勢のみ。**
4. **未測定の明記** — `:902` と world −Z 適用の nominal 把持姿勢での乖離量 = **未測定**（p11 の H-4 3 参照点が該当計器）。

## 7. 非主張

- ⛔ **owner を選ばない**（B/C owner = UNCONFIRMED / HOLD 維持）。⛔ **値を選ばない**。⛔ **方式を選ばない**（共通維持 / skill 別分割 / 観測移行のいずれも推さない）。
- ⛔ source / `[CHANGE]` / 実装 / RUN / verify / status / gate flip をしない。⛔ 旧 commit `46377eef9f` は **immutable**（本書は追加であり書き換えでない）。⛔ 他 pane の record を編集しない。07-Design / 04-Specs は CC read-only。
- taxonomy 分類は p11 材料との合流後に **p17**（T1/T2/T3 の範囲内）。
