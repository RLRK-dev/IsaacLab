# (d) arm-control — 接地記録 + substrate capability 実測（p11 ARM-CONTROL-DESIGN, 2026-07-21 13:05 JST）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** EVIDENCE v1.0（[CHECK] 段）。
**役割承継:** Rs「新規 CC を owner に」→ p4 割当（brief `ARM_CONTROL_DESIGN_ROLE_BRIEF_p11_20260721.md` @ `2887037c9f`、designation `59223eb731`）。

⛔ **本書は [CHECK] の接地 + 実測のみ。設計裁定をしない・実装しない・走らせない。**
`source` / `[CHANGE]` / `RUN` / `landing` / `push` / `training` = CLOSED のまま。census 35 不変。

---

## 0. 結論（3 行）

1. **前向き制御設計は「未着手」ではない** — banked (d) charter §1-§9（M-1〜M-6 / target scheme / gains / bar / 16 sites / stage）が実体。私の仕事は再導出でなく **新前提（裁定 A/B + P-D1 RESULT）下での再批准と前進**。
2. ⭐**新実測: 移行先候補 env7 / Newton 1.2.1 `SolverMuJoCo` は、banked 設計が要求する駆動 API を全て support する**（`joint_target_mode` / `joint_target_ke,kd` / `joint_effort_limit` / equality / mimic）。⇒ M-1(ii)・M-2・§3.1 は substrate 側で阻まれない。**CABLE joint = VBD 専用**という壁も、mujoco 枝は既に **REVOLUTE chain 化**して回避済（§3.3）。
3. ⚠**ただし LEDGER の capability 記述は VBD 軸の値**であり、env7 全体の制約として読むと **設計が実装不能に見える**。軸 qualifier が要る（§3.1）。⇒ **p0 への申し送り事項**。

---

## 1. 接地（読んだもの・file:line）

| # | source | 用途 |
|---|---|---|
| 1 | `CLAUDE.md:63-75`（DiffIK 節 / kinematic 例外）+ `.claude/rules/prohibited.md`（untracked = as-read） | 不変前提 |
| 2 | `00-DESIGN-STATUS-LEDGER.md:36` = **裁定 A**（43 step を腕とコントローラで実現・DoD = 腕/ハンド/フィンガ描画動画・UR5e×2 + Robotiq 2F-85） | 任務定義 |
| 3 | `00-DESIGN-STATUS-LEDGER.md:35` = **裁定 B**（kinematic 唯一の認可例外 = clip-retention pin = **clip 側がケーブルを保持する機構**、gripper 把持ではない。⛔不許可 = 腕関節角 直接書込 / 指の kinematic close / `update_kinematic_bodies` / weld・attachment） | 不変前提の現行版 |
| 4 | `00-DESIGN-STATUS-LEDGER.md:57` = (d) 行全文 | arc 履歴・現 gate |
| 5 | `00-DESIGN-STATUS-LEDGER.md:91-133` §DDR | [DEFER-RECON] |
| 6 | `ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md` §1-§9 / §13 @ `7ab1cc313f`（blob sha256 `b68c598dc5b32524`） | **banked 前向き設計 + P-D1 RESULT 裁定** |
| 7 | `STEP43_CONTROLLER_REALIZATION_BASELINE_RSTECHLEAD_20260721.md` @ 同 commit | 43 step 経路の現状基線 |
| 8 | `P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/`（`README.md` → `sec_14_27.md` → `P5_ANSWER_TO_P4_20260721.md`） | 任務2 の対象 |

⚠ 6 / 7 は **共有ツリーに無い or dirty** ゆえ `git show <producing commit>:<path>` で直読。
（worktree copy = HEAD 比 +704 行の未 commit 差分。dirty tree を根拠にしない。）

---

## 2. 現在地（アンカー: 確保済みの段だけを述べる）

**確保済み（banked・実測付き）**

- 前向き設計の骨格 = charter §1（M-1 wiring / M-2 ctrl ストリーム置換 / M-3 command-space / M-4 teleport⇒target-sync / M-5 ramp-in / M-6 tracking-divergence guard）・§2（per-physics-frame ctrl = 採択 A）・§3.1 gains v0（vendor 値）・§3.2 bar・§4 分類（A=11 migrate / B=5+1）・§6 stage S-0..S-3。
- **B1 = strip-at-import が PRIMARY**（charter v1.4-③、Rs 推奨に concur）。B2 零化 = strip 不可時のみ・実装者単独選択 ⛔（STOP + design delta + 再レビュー gate）。⇒ **DDR #26 の処置方針は既決**。
- **P-D1 probe RESULT（bank `e5d2dc214a`、charter §13）**:
  - 力 = **FEASIBLE**（飽和 0.0% / worst 25.1 < 28 N·m）
  - 速度帯域 = **vendor gains では不足** — 粘性 slew lag `err ≈ (kd/ke)·ω`、**T_lag = 0.2 s 一様**（400/2000 = 100/500）
  - 凍結 bar に対し **FAIL(tracking-transient)**（tr_joint 0.512 rad / tr_EE 99.9 mm vs bar 5 mrad / 3 mm）。計器は全 VALID。
  - §13 R-2 = lever は **kd/ke 比**。授権済 re-probe = **C-1 kd×0.25 / C-2 kd×0.25+ke×2**（prereg v1.3 凍結済 `b3ddfbab1c`）⇒ **07-19 の削除 directive で未起動のまま中止**。
- ⭐**L-P0 = choreography-blocked を evidence 級で CONFIRM**（§13 R-3）: 清潔基盤（B1）では banked 振付の把持連鎖が **kinematic のままでも不成立**（R0 汚染 = predicate 242/246/347 到達 / R1 清潔 = 全滅、arm q 差 ≤1.1 mrad）。⇒ **gains では直せない**。振付再工事 (W-b) = **Rs 専権 surface**。

**未確保（＝そこには居ない）**

- 43 step を物理駆動で通した実績。`wet_run_full_sequence.py` は `update_kinematic_bodies` 複写 + `SolverVBD`、`RoutingOrchestrator` は構築点 0（`STEP43…BASELINE` §1）。
- 指の忠実 actuation。MJCF `<actuator>` = parse 時 silently skip・4-bar `<equality>` = drop（`task_config.py:336-337` 逐語「the faithful actuated close is **deferred**」）。⛔「指が閉じる」を根拠にしない（p4 自己訂正・`LEDGER:37`）。
- 腕への servo target 書込は**本番コードに 0 件**（`STEP43…BASELINE` §4）。

---

## 3. ⭐ 新実測 — env7 / Newton 1.2.1 `SolverMuJoCo` の駆動 capability

**測定対象**: `/home/rlrk/env_isaaclab7/lib/python3.12/site-packages/newton`（`newton.__version__` = **1.2.1** 実測）。
**根拠**: `newton/solvers.py` support matrix（blob sha256 `a80165266f081e0b`）+ **実コードの consumption site**（docstring 単独に依存しない）。

列順 = Featherstone / SemiImplicit / XPBD / **MuJoCo** / VBD / Kamino（`solvers.py:143-150` で header 実読・以降の表も同順）。

| Model 属性 | 行 | **SolverMuJoCo** | SolverVBD | 実コード確認 |
|---|---|---|---|---|
| `joint_target_ke` / `joint_target_kd` | `:290` | ✅ yes | ✅ yes（⚠ Rayleigh 解釈 `D = kd*ke`、脚注 4 `:342`） | — |
| `joint_target_mode` | `:297` | ✅ **yes** | ⛔ no | `solver_mujoco.py:4306`/`:4962`・`kernels.py:1880,1896,1926` |
| `joint_effort_limit` | `:259` | ✅ **yes** | ⛔ no | `solver_mujoco.py:4304`・`kernels.py:2080,2121` |
| Equality（CONNECT/WELD/JOINT） | `:326` | ✅ **yes** | ⛔ no | `solver_mujoco.py:295-296` 逐語 supported |
| Mimic constraints | `:333` | ✅ **yes**（脚注 3 `:341` = REVOLUTE / PRISMATIC のみ） | ⛔ no | 同上 |
| `joint_velocity_limit` | `:267` | ⛔ no | ⛔ no | — |
| **CABLE joint** | `:200` | ⛔ **no** | ✅ **yes（VBD のみ）** | `solver_mujoco.py:292` 逐語「DISTANCE and CABLE joints are not supported」 |

表 anchor: `:137` **Joint types** / `:210` **Joint properties** / `:276` **Actuation and control** / `:312` **Constraints**。
`JointTargetMode`（`_src/sim/enums.py:134`）= NONE=0 / **POSITION=1**（`:151`）/ VELOCITY=2 / POSITION_VELOCITY=3 / EFFORT=4（`:160`）。
VBD 非対応列挙の原文 = `solver_vbd.py:119-121`（effort_limit / velocity_limit / target_mode / equality / mimic）。

### 3.1 ⚠ 軸 qualifier（本節の主要点）

`LEDGER:57` は「env7 Newton 1.2.1 の installed source 実読: … `joint_target_mode` / effort / equality / mimic = **unsupported**」と記す。
**この値は VBD 軸のもの**であり（同 clause の周辺 = VBD sites の disposition・「VBD supports none」の訂正・PS-1 POSITION-mode transfer）、`solver_vbd.py:120-121` の非対応列挙と逐語一致する。**記述は VBD について真**。

⛔ **ただし env7 全体の制約として読むと偽になる。** 同 version の `SolverMuJoCo` は上表のとおり全て support する。
⇒ **同じ「env7 が対応しない」という文字列が、solver 軸によって真偽が反転する。** 引用時は必ず solver を併記すること。
（型 = `feedback-same-constant-is-not-same-measurement-surface-2026-07-18` — 定数は同じでも measurement surface が違う。）

### 3.2 設計への帰結（事実のみ・裁定はしない）

1. **M-1(ii) の proto 配線（`joint_target_mode=POSITION` + ke/kd + effort）は env7-mujoco 上で substrate に阻まれない。** 設計変更の必要は、この軸からは**生じない**。
2. **§3.1 の effort cap（±150 / ±28 N·m、実機 spec、⛔引上げ禁止）は env7-mujoco で機構的に効く**（`joint_effort_limit` supported）。fidelity 非保守化の逃げ道が閉じている side は良い。
3. 🔶 **指の 4-bar は「substrate が禁じている」わけではない**（lead であって結論ではない）: equality = supported・mimic = supported(REVOLUTE/PRISMATIC)。env6(1.0.0) の `_init_tendons`（`solver_mujoco.py:2165`）は env7 に**存在せず** tendon 経路は再構成されている。`parse_mjcf` の `skip_equality_constraints` は既定 **False**（`import_mjcf.py:173,279,2169`）＝ THREAD 側が明示的に True を渡して落としている。
   ⛔ **未確立**: 実際に 2f85 を equality/mimic 付きで build して忠実 close が出るか。**build 実測が要る**（本書では主張しない）。
4. ⚠ VBD 軸では上記いずれも**不成立**。43 step wet driver は現在 `SolverVBD`（`STEP43…BASELINE` §1）ゆえ、**現ホストのままでは本設計は載らない**。

### 3.3 ⭐ CABLE joint wall は env7-mujoco では**既に回避済**（実測）

上表のとおり **CABLE joint = VBD 専用**（`solvers.py:200`）。素朴には「腕の actuator 駆動（MuJoCo が要る）」と「Newton CABLE ケーブル（VBD が要る）」が同一 solver で両立せず、LEDGER §FAILED-1（S1B substrate wall）と同型の壁に見える。

**実測ではこの壁は mujoco track では既に工事済**:

- `add_revolute_cable`（`test_newton_clip_routing.py:936`）docstring 逐語:「**MuJoCo rejects CABLE joints (solver_mujoco.py:292), so the mujoco branch rebuilds the cable as `add_link` capsule bodies … chained by REVOLUTE joints**」（passive bend spring は MuJoCo custom attribute、k=66.67 N·m/rad、root = FREE joint）。
- ⇒ mujoco 枝のケーブルは **REVOLUTE chain** であって Newton CABLE joint ではない。RS71 §4 の「1-DOF-per-joint PLANAR bender」記述と整合。
- `newton_route_env.py:6` 逐語 =「env7 whole-route env-core — C1->C2 DAPG (**Newton 1.2.1 SolverMuJoCo**, UR5ex2 + Robotiq koshape)」、`:591` に **backend assert**（`isinstance(self._solver, SolverMuJoCo)`、VBD-residue regression guard）。

⇒ **env7-mujoco は「REVOLUTE ケーブル + 腕 position-actuator 駆動」を同時に satisfy できる**（capability 上）。裁定 A の robot（UR5e×2 + Robotiq 2F-85）も同 env-core が既に載せている。
⚠ **ただし env-core が覆うのは C1→C2 route であって 43 step 全体ではない**。43 step driver は依然 VBD 側（§2 未確保）。**gap は substrate capability ではなく「43 step を env7 env-core 上に載せる実行体」**（= DDR #31、私の court 外）。

---

## 4. [DEFER-RECON]（§DDR × 本 chunk）

| DDR | 本 chunk との関係 | 判定 |
|---|---|---|
| **#26** P0 substrate defect（隠れ綱引き 12 本） | 前提に**する**（清潔基盤 = B1 を設計前提に置く） | **既決**（B1 = PRIMARY、charter v1.4-③）。⚠ 汚染基盤で採られた banked evidence を根拠に使わない |
| **#25** (d) 直接 joint 書込 sites | 本 chunk 本体 | 継続（census 35 不変・class は設計軸） |
| **#19** ENV-MULTIWORLD freeze（FOUNDATIONAL） | wc=1 前提で設計（charter §7-4） | 非 block（wc>1 は per-world readback assert が後段） |
| **#31** 実行 driver 不在（`RoutingOrchestrator` 構築点 0） | 43 step を通す実行体が無い | ⛔**本 chunk の外**（所管 = pX+pS が職掌決定・Rs 08:2x）。⚠ **私の制御設計だけでは 43 step は走らない** |
| **#29** demo 198 本の再記録 | choreography 再工事と単一 event | Rs 専権（W-b） |
| **#35** guard 述語不一致 | commit 時 `--no-verify` 必要 | 適用（本 commit も該当） |
| #2 / #4 / #12 | pin arc (d-a)/(d-b) 系。⚠ 各行の「pin 削除 directive 波及」注記は **裁定 B で前提が戻った**ため再照合が要る | ⛔ **私の所管外**（pin node 側）。surface のみ |

**FOUNDATIONAL 未解決による着手不可は無し。** ただし §5 の 2 件は私の court に無い。

---

## 5. 私の court に無い決定（p4 経由で Rs へ上げる要ありと考える 2 件）

1. **substrate 確定** — 43 step 実現先を env7-mujoco とするか。
   p4 は「公算が高い（**推定**・裁定でない）」と明記（`STEP43…BASELINE` §0-3 / §6）。`LEDGER:57` も「B0/B1 は env7-MuJoCo へ移管 — **未決・Rs 裁定待ち**〔substrate 移管を含むため Rs 専権〕」。
   ⭐**本書 §3 で技術的障害は 3 つとも消えた**（駆動 API 対応 / effort cap 機構的に有効 / CABLE 壁は REVOLUTE 化で回避済）。⇒ **残っているのは capability 問題ではなく authority 問題**（substrate 移管 = Rs 専権）。
   ⚠ **私は「env7-mujoco にせよ」と裁定しない。** 実測が言えるのは「**その先なら制御設計側は阻まれない**」までで、移管の可否・費用・B0/B1 影響は私の court に無い。
2. **振付（choreography）の扱い** — L-P0 が「清潔基盤では banked 振付の連鎖が成立しない」を evidence 級で確定させている。gains では直せない（§13 R-3）。
   ⇒ 43 step を**現 banked 振付のまま**実現するのか、**再工事**するのか（W-b = Rs 専権）で、私の設計対象が変わる。
   ⚠ §13 R-3 付帯の forward 要件 = 再記録振付には **摂動耐性 leg（≥ trainer residual / DR scale）を必須化**（1 mrad で flip する振付を再び bank しない）。

---

## 6. 任務2（§14.27 bank 可否）— 現時点の所見のみ（裁定は次段）

読了済。verdict の骨子（単一 class DRIVE / bind = 全 consumer / fence F-α・F-β / [H-1] / 訂正 #27 / citation 訂正 `:506`→`:483`）は、**論証が閉クエリと構造判定で自足しており、所管移動によって無効化される種類のものではない**、というのが現時点の所見。

⚠ ただし **bank 前に少なくとも 1 点の再照合が要る**: §14.27 (4) は untracked pin wrapper `_pp` の escalation 根拠を **「Rs 2026-07-19『kinematic 完全削除（pin 含む）』directive の射程内」**に置いている。**この前提は裁定 B で覆っている。**
- F-β の disposition 義務（track / 削除 / 実行不能証拠つき登録）は untracked 性に由来するので**独立に生きる**。
- しかし `_pp` が `jq[ARM_Q:]`（= 両腕を除いた cable 側）を 0 埋めする機構が、裁定 B の認可例外「**clip 側がケーブルを保持する機構**」に当たるのか、それとも cable 全体の凍結という別物なのかは、**実体を読んでから**でないと言えない。未読。
- ⇒ **bank 可否の裁定は、この 1 点を実測してから出す。**

---

## 7. 非主張（明示）

- 設計裁定をしていない。class を選んでいない。bar を動かしていない。
- §3 は **capability の実測**であって、「env7-mujoco で動く」「PD で 43 step が通る」の主張ではない。
- 指の 4-bar 復元は **lead**（build 実測前）。「できる」と言っていない。
- 物理妥当性の判定はしない（最終基準 = Rs の動画 human-GT）。

## 8. L 自己申告

**L1**（新規 file 1 本・records のみ・コード 0・設計裁定 0・rule file 非接触）。
新規 file 作成は形式上 L2 trigger だが、**設計裁定を含まない [CHECK] 実測記録**ゆえ p4 `STEP43_CONTROLLER_REALIZATION_BASELINE`（同型・records 軸で bank）の先例に合わせた。**降格が不適なら指摘を受ける。**
commit = explicit pathspec + `--no-verify`（DDR #35）。
