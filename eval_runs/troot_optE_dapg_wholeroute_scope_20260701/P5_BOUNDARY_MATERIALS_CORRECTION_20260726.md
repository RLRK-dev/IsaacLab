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

⭐ **行番号が指す tree = 読取時の working tree**（banked tree ではない）。
⚠**R1 訂正 2026-07-26**: 旧記載の「読取 2026-07-26T17:2x–17:35 JST」は **非 exact ゆえ撤回**（時刻を合成しない）。確実に言えるのは **bank commit `46377eef9f79efc20acc7e8bfdee739c5f35a09c`（author `2026-07-26T17:35:22+09:00`）より前に読んだ**ことのみで、**per-read の時刻は未記録**。
⭐**R1 に従い WT 行を historical / 非 evidence へ格下げ**: 下表の `as_read (WT)` 列は **retrievable committed bytes を持たない**ため **evidence として用いない**。**本書の evidential な主張はすべて banked commit `46377eef9f79efc20acc7e8bfdee739c5f35a09c` にのみ接地する**（⚠C4: 「operative」を分類語として使わない）。
⭐**用語の分離（R1）**: 旧 `changed` → **`modified_vs_banked`**（banked と WT が異なる path）。**`changed_during_read` は別概念であり本書では未記録＝主張しない**（読取中の変化を測っていない）。

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
| `harness/scripts/predict_training.py` | ⛔**untracked** | **ABSENT（commit tree に不在）** | ⚠**ABSENT / N/A**〔**R4 訂正**: 不在に blob SHA は存在しない。旧記載の `e3b0c442…` は空入力の sha256 であって blob SHA ではないため **banked 列から撤回**〕 | （historical・非 evidence・as_read 値の full 64-hex: `7117860535ad2c95a9377eb85c7aa853d93a2e5d085a57b59ffdecffa7ee3401`） |

**`modified_vs_banked = [newton_grip_env.py, newton_approach_cable_mujoco_env.py, step_table.py, test_newton_clip_routing.py, newton_routing_utils.py]`／`untracked = [harness/scripts/predict_training.py]`（ABSENT）／`clean = 残り 7 path`。**
⚠**`changed_during_read` = 未記録（unmeasured）** — 読取中に変化しなかったという主張はしない（R1）。

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

### 2-b. banked vs WT の 全 delta（10 件） — ⚠**R2 訂正: 本表は evidence ではなく「旧数値がなぜ違ったか」の historical explanation（再現不能）**
⛔ **evidence は §2-a の banked 計数のみ**（`EE_TO_FINGERTIP` 17 file/68 hit・`GRASP_Z` 22 file/105 hit・`PUSH_Z` 13 file/55 hit）。
⚠ 本表の WT 側の値は committed bytes を持たず再現できない。特に `harness/orchestrator/harness_integration_test.py`・`thread_isaac_lab/tests/test_env_refactor_bit_identical.py`・`thread_isaac_lab/tests/test_env_refactor_helpers.py` の 3 path は **§1 の 13-path source manifest に含まれず taxonomy / full SHA の被覆も無い** ⇒ **evidence として用いない**（historical explanation に留める）。

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

### 2-c. 役割分類（banked・**source-role candidate のみ列挙**。probe-script は集計のみ）
⚠**C4 訂正**: 旧ラベル `operative-candidate` / `operative path` を **撤回**。runtime status が UNVERIFIED である限り `operative` を分類語に使わない ⇒ **`source-role candidate`（path 由来の構造分類）** に改称。

| 定数 | source-role candidate（file:hit） | probe-script |
|---|---|---|
| `EE_TO_FINGERTIP` | `configs/task_config.py`:5 / `envs/newton_grip_env.py`:3 / `envs/newton_skill_env_base.py`:3 / `configs/mpc_config_ic.py`:1 | 13 file / 56 hit |
| `GRASP_Z` | `configs/task_config.py`:3 / `envs/newton_grip_env.py`:3 / `configs/mpc_config_grip.py`:1 / `envs/newton_approach_cable_mujoco_env.py`:1 / `envs/route_executor.py`:1 | 17 file / 96 hit |
| `PUSH_Z` | `envs/newton_grip_env.py`:3 / `skills/scripted_skills.py`:2 / `skills/step_table.py`:2 / `configs/task_config.py`:1 / `envs/route_executor.py`:1 | 8 file / 46 hit |

⚠⚠ **分類は path 由来の役割であって稼働証明ではない（liveness は UNVERIFIED）。** pN の「tracked `*.py` だけから live を推論しない」に従い、以下を明記する:
- ⭐ **反例あり**: `scripts/newton_routing_utils.py` は path 上 probe-script だが、**`envs/route_executor.py`（`:1910`/`:2144`/`:3040`/`:3041`/`:3893`）と `skills/scripted_skills.py`（`:124`/`:244`/`:288`/`:336` 他）から import される library**（banked 実測）。⇒ **path bucket ≠ reachability**（本 arc で私が別件で立てた指摘と同型）。
- `envs/route_executor.py` の `GRASP_Z`/`PUSH_Z` hit は **legacy 宣言そのもの**（`:2450`「LEGACY P1-P4 path, NOT used by `route_c1_c2`」）⇒ **source-role candidate に属するが、当該 hit は legacy 宣言であって消費ではない**（⚠C4: 旧「operative path」表現を撤回）。
- ⇒ **source-role / legacy / harness / test / probe / snapshot の確定分類には runtime 証拠（実行経路）が要る。本書は静的分類に留める。**（⚠C4: 分類語から `operative` を除去）

### 2-d. 自己検出した query 欠陥（記録）
本訂正の作業中、`git grep … -- 'thread_isaac_lab/skills/**/*.py'` が **`skills/` 直下の file に一致せず 0 hit** を返した。0 を不在の根拠にせず検索対象集合（`skills/` の `*.py` = 5 file）を確認して pathspec を `'thread_isaac_lab/skills/'` に修正した結果、上記の library import が判明した。⇒ **pathspec の `**` は直下を覆わない**ことを本書に記録する。

---

## 3. B3 訂正 — 自 artifact 内の矛盾

**RETRACT（旧 artifact `:32`）**: 「| `task_config.py:93` / `:95` | `GRASP_Z` / `PUSH_Z` を導出 | **全 skill 横断（下流全部）** |」の **「全 skill 横断（下流全部）」**。
⇒ 旧 artifact 自身の `:54` / `:81` / `:115` が「approach(mujoco) と route は非消費」と正しく述べており、`:32` はそれと矛盾していた。

**正**: `task_config.py:93`/`:95` の**派生先は `GRASP_Z` / `PUSH_Z` の 2 定数**。その consumer は §2-c の source-role candidate 集合（`newton_grip_env` / `scripted_skills` / `step_table` / `mpc_config_grip` / `task_config` 内部）＋ probe-script 群。⛔ **`approach`(mujoco) と `route_c1_c2` は非消費**（`newton_approach_cable_mujoco_env.py:197`／`route_executor.py:2450`）。
⇒ ⭐ **「全 skill 共通は現状の事実でない」という結論は保持**（B3 は要約行の誤りであり結論の誤りではない）。

---

## 4. B4 訂正 — 「観測移行の live 先例」を格下げ

**RETRACT（旧 artifact §1(4) / §4③）**: 「Z-Check が **finger body z** を定数なしで直読 ⇒ **観測移行の live 先例**」および「index 規約が **2 つ対等に併存**」。

**保持する事実（banked）**: `test_newton_clip_routing.py:466` = `body_q[bs + EE_BODY_OFFSET][2]`（hand z）／`:468-469` = `body_q[bs+7][2]`, `body_q[bs+8][2]` ⇒ **生の BODY-space index による per-body z 読み取りが banked source（`46377eef9f`）に存在する**。⚠**R3 訂正**: 旧記載「live code に存在する」を撤回 — **source の存在であって runtime 到達性ではない**（本書 §2-c の liveness=UNVERIFIED と整合）。

⛔ **UNVERIFIED へ移す**: その `+7` / `+8` が **pad / finger body かは未検証**。SSOT は pad-carrying followers を **`[9, 13]`** と定義（`task_config.py:37` `GRIPPER_PAD_BODY_IDX = [9, 13]  # BODY space: pad-carrying followers`／`:48` `FINGER_LOCAL = GRIPPER_PAD_BODY_IDX  # [9,13] (BODY-space finger-pos reads)`）。同 `:47` `EE_BODY_OFFSET = 5` と同じ BODY 空間の index 系である。
⇒ **`+7`/`+8` と `[9,13]` は stale / mismatch の候補**であり、「対等な 2 規約」ではない（pN 指摘どおり）。**同一性が解決するまで pad/finger としての妥当性は UNVERIFIED。**

⇒ ⚠⚠**R5 訂正（私の過剰撤回）**: 旧記載「⛔ 既存の read が pad を観測している証拠は無い」は **過剰であり撤回**。**正しい区別**:
- ✅ **pad-body の source read は存在する** — banked `newton_grip_env.py:660` `_apply_finger_spring` が `:667-668` で `for lf in FINGER_LOCAL: bi = ws + arm_offset + lf`（= SSOT の pad index `[9,13]`）を導出し、`:670` `pos = body_q[bi][:3]` / `:671` `vel = body_qd[bi][3:6]` を **読んでいる**。⇒ 「pad を指す read が無い」は誤り。
- ⛔ **UNVERIFIED のまま残るのは 2 点**: ①**production reachability**（この経路が実運用で通るか）②**要求された観測面 / 測定面としての用途**（当該 read の用途は `:673-674` の spring force 印加であって閾値の測定面ではない）。
- ⇒ 「観測量へ移せる」の根拠 = **asset に pad body が実在**（`2f85_koshape.xml:107`/`:154`）**＋ SSOT index 経由の pad read が banked source に実在**。⚠ ただし **測定面としての採用実績は無い**。
- ⚠ `+7`/`+8`（`test_newton_clip_routing.py:468-469`）の同一性は **依然 UNVERIFIED**（SSOT の pad は `[9,13]`）= stale / mismatch 候補。

---

## 5. B5 訂正 — 「物理接触面 = f1ext 爪先」を UNMEASURED へ

**RETRACT（旧 artifact §1(2)）**: 「物理接触が起きる面は **コ f1ext 爪先**」。

**保持する asset 幾何事実**: pad body（`:107`/`:154`）／その上の geom `right_pad_f1ext`・`right_pad_f2ext`（`:116`/`:117`・local `pos` 明記）／`EE_TO_PINCH_TIP_CLOSED` は「pad TIP drop（コ f1ext claw tip）」を測った値という**記述**（`task_config.py:321`）。

⛔ **実際の接触 geom は UNMEASURED。** 反証材料（banked `route_executor.py:2436-2440`）:
- `:2436-2437` 逐語「retention = the cable is **SANDWICHED between the two claws (f1ext bottom + f2ext top**, mouth ~10mm, Ø8 cable -> ~2mm play; `GD-KoShape-Finger.md:51-58`)」
- `:2438` 逐語「The OLD **f1ext-only** gate false-FAILed "cable risen to the TOP claw under drag"」
⇒ **単一 geom を接触面と断定できない**（⚠**C3 訂正**: 旧記載「live gate」を撤回 — **banked source の retention 述語**〔`route_executor.py:2436-2440` の comment ＋ 判定式〕が両爪＋横方向 footprint で定義している、が正。**source の記述であって runtime 到達性の主張ではない**）。接触面の同定には測定が要る。

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

---

## 8. R1-R6 訂正記録（pN RETURN `MSG-PN-P5-FINGERTIP-MATERIALS-CORRECTION-RETURN-20260726-002`）

⚠**C2 訂正**: 旧記載「発行 2026-07-26T18:03:24+09:00」は **誤り（＝私の作業時刻を pN の発行時刻として書いた）ゆえ撤回**。
**pN RETURN の発行時刻 = `2026-07-26 18:00:50 JST`**（pN message の stamp 逐語）。⛔ 受信・処理時刻をこの欄に代入しない。
本節の追記が着地した記録 = bank commit `b5d4a3d4887de8088c8361eaaac000bab97ed12b`（author `2026-07-26T18:04:26+09:00`）。

| # | pN 指摘 | 本書での処置 |
|---|---|---|
| **R1** | 非 exact 時刻 `17:2x-17:35`／dirty-WT hash に pre-post bracket も retrievable bytes も無い／`changed` の語が混在 | **時刻主張を撤回（合成しない）**・**WT 行を historical / 非 evidence へ格下げ**し evidential 主張を banked `46377eef9f` のみに接地・**`changed` → `modified_vs_banked`**、**`changed_during_read` は未記録＝主張しない**（§1 冒頭） |
| **R2** | WT-only delta が manifest 外 3 path を evidence に使用 | **delta 表を historical explanation（再現不能）へ格下げ**・evidence は §2-a の banked 計数のみ・当該 3 path は manifest 外＋SHA 未被覆ゆえ非 evidence と明記（§2-b） |
| **R3** | 「live code」と liveness=UNVERIFIED が矛盾 | **「banked source に存在する」へ改め**、runtime 到達性を推論しない（§4） |
| **R4** | ABSENT path に空入力 SHA を割当 | **ABSENT / N/A** に改め、空入力 sha256（`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`）を banked 列から撤回（§1 表） |
| **R5** | ⚠**私の過剰撤回** — banked `newton_grip_env.py:644-675` は `FINGER_LOCAL=[9,13]` 由来 index で `body_q`/`body_qd` を読む | **過剰撤回を撤回**し正しい区別を記載: **pad-body source read は存在**（`:660`/`:667-668`/`:670`/`:671`）／**production reachability と「要求された観測・測定面としての用途」は UNVERIFIED**（当該 read の用途は `:673-674` の spring force）（§4） |
| **R6** | wrapped historical artifact に live / two-regime の残留 | **旧本文全体を HISTORICAL / SUPERSEDED 境界の内側に置き**、`:18`/`:64-65`/`:125`/`:131` の live・「2 つ併存」表現を個別に narrow（対象 = materials artifact 側） |

⛔ **PASS 済の事実は保持**（correction/wrapped SHA256・old pin 一致・banked path hash・68/105/55 計数・B3/B5 の方向・authority fence）。⛔ owner / 値 / 方式は非選択維持。source / `[CHANGE]` / 実装 / RUN / verify / status / gate flip = CLOSED。旧 commit（`46377eef9f`・`44f3c8af3e`）は immutable。

## 9. C1-C4 訂正記録（pN RETURN `MSG-PN-P5-FINGERTIP-MATERIALS-R1R6-RETURN-20260726-003`・発行 `2026-07-26 18:07:08 JST`）

| # | pN 指摘 | 処置 |
|---|---|---|
| **C1** | `git show --check` FAIL（本 file `:184` に EOF の新規空行） | **EOF を単一改行へ修正**し `git show --check` clean を確認。旧 commit `b5d4a3d488` は保存（records-only の後継 commit で着地） |
| **C2** | §8 が pN RETURN 発行を `18:03:24+09:00`（= 私の作業時刻）と誤記録 | **虚偽の `18:03:24` を撤回**し **pN 発行 = `2026-07-26 18:00:50 JST`（stamp 逐語）** を記載。⛔ 受信・処理時刻を代入しない。私の追記の着地は bank commit の author 時刻で示す |
| **C3** | 「live gate」が同 artifact の liveness=UNVERIFIED と矛盾 | **banked source の retention 述語（comment＋判定式）** という source-only 表現へ改め、runtime 到達性を主張しない |
| **C4** | `operative-candidate` / `operative path` を分類語に使用／`:41` に切り詰め digest | 分類語を **`source-role candidate`** へ全面改称し `operative` を分類語から除去（`:24`/`:99`/`:101`/`:109`/`:110`/`:122`/`:176`）。`:41` の as_read digest を **full 64-hex に展開**、`:179` の `e3b0c442…` も full 展開（partial hash は historical でも exact pin でない） |

⛔ **PASS 済は保持**（WT demotion・`modified_vs_banked` 分離・manifest 外 delta の格下げ・ABSENT/N-A・pad-source-read 訂正・historical 境界・banked 計数/pins・B3/B5 方向・authority fence）。⛔ **新たな値 / owner / 方式の選択なし・実装 gate なし。**
